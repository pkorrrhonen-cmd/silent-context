"""The claim store: SQLite tables for entities, edges, claims, sources and evidence.

The store is derived. It is rebuilt from the files in `data/` and never committed, so a clean
install has a working store without a binary in the repository.

Two clocks are kept apart. `valid_from` and `valid_to` are world time and may be NULL, because an
unknown time stays unknown. `received_at` and `superseded_at` are information time. Status (active,
recheck, disputed and so on) is not stored: it is computed at read time for a claim and a unit.
"""

import argparse
import json
import os
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "data" / "seed" / "entities.json"

SCHEMA = """
CREATE TABLE entity (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN
    ('node', 'device_class', 'procedure_type', 'site', 'access_barrier', 'group')),
  name TEXT NOT NULL,
  attrs TEXT NOT NULL DEFAULT '{}'
);

-- src and dst are entity or claim ids, so they carry no foreign key.
CREATE TABLE edge (
  src TEXT NOT NULL,
  rel TEXT NOT NULL CHECK (rel IN
    ('INSTANCE_OF', 'LOCATED_AT', 'HAS_BARRIER', 'ABOUT', 'APPLIES_TO', 'SUPERSEDES',
     'CONFLICTS_WITH')),
  dst TEXT NOT NULL,
  valid_from TEXT,
  valid_to TEXT
);

CREATE TABLE claim (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('troubleshooting', 'access')),
  claim_text TEXT NOT NULL,
  symptom TEXT,
  observed_entity TEXT REFERENCES entity(id),
  scope_text TEXT,
  scope_status TEXT NOT NULL DEFAULT 'undefined' CHECK (scope_status IN ('confirmed', 'undefined')),
  applies_to TEXT REFERENCES entity(id),
  -- What the agent's next step reads. There is no step machine: the order also stays in claim_text.
  check_step TEXT,
  check_kind TEXT CHECK (check_kind IN ('read_counters', 'other')),
  action TEXT,
  action_kind TEXT NOT NULL DEFAULT 'none' CHECK (action_kind IN
    ('read', 'bounce_interface', 'reboot', 'replace_hw', 'none')),
  do_not_before TEXT,
  valid_from TEXT,
  valid_from_basis TEXT CHECK (valid_from_basis IN ('stated', 'anchored')),
  valid_to TEXT,
  valid_to_basis TEXT CHECK (valid_to_basis IN ('stated', 'superseded_end_unknown')),
  received_at TEXT NOT NULL,
  superseded_at TEXT,
  binding_status TEXT NOT NULL CHECK (binding_status IN ('bound', 'waiting')),
  binding_reason TEXT,
  -- A world time always says where it came from: time is not invented.
  CHECK ((valid_from IS NULL) = (valid_from_basis IS NULL)),
  CHECK (valid_to IS NULL OR valid_to_basis = 'stated'),
  -- An unclear binding waits with its reason; a bound claim names its entity.
  CHECK (binding_status = 'bound' OR binding_reason IS NOT NULL),
  CHECK (binding_status = 'waiting' OR observed_entity IS NOT NULL)
);

-- teller_key exists only to merge one person's accounts of a claim. It never leaves the store.
CREATE TABLE source (
  id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES claim(id),
  channel TEXT NOT NULL CHECK (channel IN ('teams', 'email', 'transcript')),
  ref TEXT NOT NULL,
  role TEXT,
  teller_key TEXT,
  excerpt TEXT,
  source_time_text TEXT,
  received_at TEXT NOT NULL
);

CREATE TABLE evidence_event (
  id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES claim(id),
  scope_entity TEXT REFERENCES entity(id),
  type TEXT NOT NULL CHECK (type IN
    ('told', 'reported_success', 'reported_failure', 'disputed', 'superseded', 'flagged')),
  event_time TEXT,
  source_ref TEXT,
  excerpt TEXT,
  channel TEXT,
  role TEXT,
  basis TEXT NOT NULL CHECK (basis IN ('message', 'telemetry', 'flag'))
);

CREATE TABLE event (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN
    ('module_replaced', 'link_up', 'admin_down', 'admin_up', 'firmware_updated', 'config_changed')),
  entity TEXT NOT NULL REFERENCES entity(id),
  port TEXT,
  event_time TEXT NOT NULL,
  attrs TEXT NOT NULL DEFAULT '{}'
);

-- The counters the agent can read itself. Time-series data is time-aware by nature.
CREATE TABLE telemetry (
  entity TEXT NOT NULL REFERENCES entity(id),
  port TEXT NOT NULL,
  t TEXT NOT NULL,
  metric TEXT NOT NULL,
  value INTEGER NOT NULL
);

-- Someone's estimate about a unit, kept as that with its source. It never becomes a graph fact.
CREATE TABLE estimate (
  id TEXT PRIMARY KEY,
  entity TEXT NOT NULL REFERENCES entity(id),
  attribute TEXT NOT NULL,
  value_text TEXT NOT NULL,
  role TEXT,
  source_ref TEXT NOT NULL,
  received_at TEXT NOT NULL
);

-- Every source read, also when it held no claim, with the checksum of what was read.
CREATE TABLE ingest_log (
  file TEXT PRIMARY KEY,
  sha256 TEXT NOT NULL,
  channel TEXT NOT NULL,
  received_at TEXT NOT NULL,
  claim_ids TEXT NOT NULL DEFAULT '[]',
  mode TEXT NOT NULL CHECK (mode IN ('model', 'recorded'))
);

CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE answer_log (
  id TEXT PRIMARY KEY,
  asked_at TEXT NOT NULL,
  entity TEXT,
  symptom TEXT,
  tier TEXT NOT NULL CHECK (tier IN ('propose', 'check_first', 'unknown')),
  next_step TEXT,
  action_kind TEXT CHECK (action_kind IN ('read', 'bounce_interface', 'reboot', 'replace_hw', 'none')),
  claim_ids TEXT NOT NULL DEFAULT '[]',
  who_acts TEXT CHECK (who_acts IN ('agent', 'person', 'ask')),
  who_why TEXT,
  human_did TEXT,
  done_by TEXT CHECK (done_by IN ('person', 'agent')),
  outcome TEXT
);

-- What the agent could not answer, and who to ask. The first half of a question at the moment of need.

CREATE TABLE gap_log (
  id TEXT PRIMARY KEY,
  asked_at TEXT NOT NULL,
  entity TEXT,
  symptom TEXT,
  ask_group TEXT
);
"""


def store_path() -> Path:
    return Path(os.environ.get("STORE_PATH") or ROOT / "store" / "claims.db")


def _open(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed(conn: sqlite3.Connection, seed_file: Path = SEED_FILE) -> None:
    data = json.loads(seed_file.read_text(encoding="utf-8"))
    conn.executemany(
        "INSERT INTO entity (id, kind, name, attrs) VALUES (?, ?, ?, ?)",
        [
            (e["id"], e["kind"], e["name"], json.dumps(e["attrs"], ensure_ascii=False, sort_keys=True))
            for e in data["entities"]
        ],
    )
    known = {e["id"] for e in data["entities"]}
    for edge in data["edges"]:
        unknown = {edge["src"], edge["dst"]} - known
        if unknown:
            raise ValueError(f"Seed edge names unknown entities: {sorted(unknown)}")
    conn.executemany(
        "INSERT INTO edge (src, rel, dst, valid_from, valid_to) VALUES (?, ?, ?, ?, ?)",
        [
            (e["src"], e["rel"], e["dst"], e.get("valid_from"), e.get("valid_to"))
            for e in data["edges"]
        ],
    )


def build(path: Path | None = None) -> Path:
    """Build a fresh store from the seed files and move it into place in one step."""
    path = path or store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    os.close(handle)
    temp = Path(temp_name)
    try:
        conn = _open(temp)
        try:
            conn.executescript(SCHEMA)
            seed(conn)
            conn.commit()
        finally:
            conn.close()
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return path


@contextmanager
def session(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """A connection that commits on success. A missing store is built first."""
    path = path or store_path()
    if not path.exists():
        build(path)
    conn = _open(path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the claim store from the files in data/.")
    parser.add_argument(
        "--seed",
        action="store_true",
        required=True,
        help="Rebuild the store from the seed graph. The store is derived, so nothing is lost.",
    )
    parser.parse_args()
    path = build()
    with session(path) as conn:
        entities = conn.execute("SELECT count(*) FROM entity").fetchone()[0]
        edges = conn.execute("SELECT count(*) FROM edge").fetchone()[0]
    print(f"{path}: {entities} entities, {edges} edges")


if __name__ == "__main__":
    main()

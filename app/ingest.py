"""From sources to claims: reads each source, extracts, binds, merges and records the evidence.

The demo clock decides what is known. A source counts once the clock has passed its `received_at`,
and an event once it has passed its time. The store is rebuilt on every run, because recorded model
answers make that free and it keeps every state of knowledge reproducible.
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

from app import db, events, extract, llm
from app.extract import ExtractedClaim
from app.resolve import Binding, Graph, resolve_target
from app.sources import ROOT, SOURCES_DIR, Message, Thread, appears_in, load_manifest, parse

TELEMETRY_DIR = ROOT / "data" / "events"
EVENTS_FILE = TELEMETRY_DIR / "events.json"

# An event only anchors a claim's start if it happened shortly before the conversation about it.
ANCHOR_WINDOW = timedelta(hours=24)
EVENT_OF_PROCEDURE = {"PROC-SFP-REPLACE": "module_replaced"}
DAYS_AGO = {"today": 0, "yesterday": 1, "the day before yesterday": 2}


def load_events(conn: sqlite3.Connection, until: str | None) -> None:
    stream = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))["events"]
    conn.executemany(
        "INSERT INTO event (id, type, entity, port, event_time, attrs) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (e["id"], e["type"], e["entity"], e["port"], e["event_time"], json.dumps(e["attrs"]))
            for e in stream
            if until is None or e["event_time"] <= until
        ],
    )


def load_telemetry(conn: sqlite3.Connection, until: str | None) -> None:
    for path in sorted(TELEMETRY_DIR.glob("telemetry_*.json")):
        series = json.loads(path.read_text(encoding="utf-8"))
        conn.executemany(
            "INSERT INTO telemetry (entity, port, t, metric, value) VALUES (?, ?, ?, ?, ?)",
            [
                (series["node"], series["port"], s["t"], series["metric"], s["value"])
                for s in series["samples"]
                if until is None or s["t"] <= until
            ],
        )


def _next_id(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    return f"{prefix}-{count + 1:03d}"


def _message_time(thread: Thread, message: Message, received_at: str) -> str | None:
    """A message's time. A message with only a clock time takes the day of the export it came in."""
    if not message.time:
        return None
    return f"{thread.day or received_at[:10]}T{message.time}:00"


def _teller_key(claim_id: str, author: str | None) -> str:
    """Per claim on purpose: it can merge one person's accounts of a claim, and nothing else."""
    name = " ".join((author or "unknown").split()).casefold()
    return hashlib.sha256(f"{claim_id}|{name}".encode("utf-8")).hexdigest()[:12]


def _literal(thread: Thread, values: list[str]) -> list[str]:
    """Only what is really in the text counts. A value the model made up is dropped here."""
    text = thread.full_text()
    return [value for value in values if appears_in(value, text)]


def _literal_or_none(thread: Thread, value: str | None) -> str | None:
    return value if value and appears_in(value, thread.full_text()) else None


def _ref(thread: Thread, messages: list[Message]) -> str:
    if thread.channel == "email":
        return thread.file
    return f"{thread.file}#seq={','.join(str(m.seq) for m in messages)}"


def _add_edge(conn: sqlite3.Connection, src: str, rel: str, dst: str) -> None:
    exists = conn.execute(
        "SELECT 1 FROM edge WHERE src = ? AND rel = ? AND dst = ?", (src, rel, dst)
    ).fetchone()
    if not exists:
        conn.execute("INSERT INTO edge (src, rel, dst) VALUES (?, ?, ?)", (src, rel, dst))


def _add_evidence(
    conn: sqlite3.Connection,
    thread: Thread,
    message: Message,
    claim_id: str,
    kind: str,
    scope: str | None,
    event_time: str | None,
    source_ref: str,
    excerpt: str | None,
) -> None:
    conn.execute(
        "INSERT INTO evidence_event (id, claim_id, scope_entity, type, event_time, source_ref,"
        " excerpt, channel, role, basis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'message')",
        (
            _next_id(conn, "evidence_event", "evd"),
            claim_id,
            scope,
            kind,
            event_time,
            source_ref,
            excerpt,
            thread.channel,
            message.role,
        ),
    )


def _valid_from(
    conn: sqlite3.Connection,
    thread: Thread,
    item: ExtractedClaim,
    entity: str | None,
    received_at: str,
) -> tuple[str | None, str | None]:
    """A claim's start in world time, and its basis. Otherwise both stay empty: time is not invented."""
    if item.kind == "access":
        if not thread.day:
            return None, None
        days = 0
        if item.relative_time:
            days = DAYS_AGO.get(item.relative_time.strip().casefold(), -1)
            if days < 0:
                return None, None
        start = datetime.strptime(thread.day, "%Y-%m-%d") - timedelta(days=days)
        return start.strftime("%Y-%m-%d"), "stated"

    event_type = EVENT_OF_PROCEDURE.get(item.procedure_type or "")
    started = _message_time(thread, thread.messages[0], received_at)
    if not (entity and event_type and started):
        return None, None
    row = conn.execute(
        "SELECT event_time FROM event WHERE entity = ? AND type = ? AND event_time <= ?"
        " ORDER BY event_time DESC LIMIT 1",
        (entity, event_type, started),
    ).fetchone()
    if row is None:
        return None, None
    gap = datetime.fromisoformat(started) - datetime.fromisoformat(row["event_time"])
    return (row["event_time"], "anchored") if gap <= ANCHOR_WINDOW else (None, None)


def _new_claim(
    conn: sqlite3.Connection,
    graph: Graph,
    thread: Thread,
    item: ExtractedClaim,
    received_at: str,
) -> str:
    binding: Binding = resolve_target(
        graph,
        item.kind,
        _literal(thread, item.target_node_ids),
        _literal(thread, item.target_sites),
        _literal(thread, item.target_ports),
        _literal_or_none(thread, item.target_firmware),
        item.mentions_barrier,
    )
    scope_text = _literal_or_none(thread, item.scope_text)
    version = _literal_or_none(thread, item.scope_names_version)
    applies_to = graph.class_for_version(version) if version else None
    valid_from, basis = _valid_from(conn, thread, item, binding.entity, received_at)
    claim_id = _next_id(conn, "claim", "clm")
    conn.execute(
        "INSERT INTO claim (id, kind, claim_text, symptom, observed_entity, scope_text, scope_status,"
        " applies_to, check_step, check_kind, action, action_kind, do_not_before, valid_from,"
        " valid_from_basis, received_at, binding_status, binding_reason)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            claim_id,
            item.kind,
            item.claim_text,
            item.symptom,
            binding.entity,
            scope_text,
            "confirmed" if applies_to else "undefined",
            applies_to,
            item.check_step,
            item.check_kind,
            item.action,
            item.action_kind,
            item.do_not_before,
            valid_from,
            basis,
            received_at,
            "bound" if binding.entity else "waiting",
            binding.reason,
        ),
    )
    if binding.entity:
        _add_edge(conn, claim_id, "ABOUT", binding.entity)
        site = next(
            (site for site, barriers in graph.barriers_of_site.items() if binding.entity in barriers),
            None,
        )
        if site:
            _add_edge(conn, claim_id, "ABOUT", site)
    if item.procedure_type in graph.procedures:
        _add_edge(conn, claim_id, "ABOUT", item.procedure_type)
    if applies_to:
        _add_edge(conn, claim_id, "APPLIES_TO", applies_to)
    return claim_id


def _narrow_scope(
    conn: sqlite3.Connection, graph: Graph, thread: Thread, item: ExtractedClaim, claim_id: str
) -> None:
    """A later message can narrow a claim's scope. The earlier words stay next to the new ones."""
    words = _literal_or_none(thread, item.scope_text)
    if not words:
        return
    version = _literal_or_none(thread, item.scope_names_version)
    applies_to = graph.class_for_version(version) if version else None
    claim = conn.execute(
        "SELECT scope_text, scope_status, applies_to FROM claim WHERE id = ?", (claim_id,)
    ).fetchone()
    old = claim["scope_text"]
    if applies_to:
        text = f"{old}; {words}" if old and words.casefold() not in old.casefold() else words
        conn.execute(
            "UPDATE claim SET scope_text = ?, scope_status = 'confirmed', applies_to = ? WHERE id = ?",
            (text, applies_to, claim_id),
        )
        _add_edge(conn, claim_id, "APPLIES_TO", applies_to)
    elif not old:
        conn.execute("UPDATE claim SET scope_text = ? WHERE id = ?", (words, claim_id))


def _supersede(
    conn: sqlite3.Connection,
    thread: Thread,
    message: Message,
    old_id: str,
    new_id: str,
    received_at: str,
    ref: str,
    when: str | None,
) -> None:
    """The old claim stays. Its end is the new claim's start, or stays unknown if that is unknown."""
    start = conn.execute("SELECT valid_from FROM claim WHERE id = ?", (new_id,)).fetchone()[0]
    conn.execute(
        "UPDATE claim SET superseded_at = ?, valid_to = ?, valid_to_basis = ? WHERE id = ?",
        (received_at, start, "stated" if start else "superseded_end_unknown", old_id),
    )
    _add_edge(conn, new_id, "SUPERSEDES", old_id)
    observed = conn.execute("SELECT observed_entity FROM claim WHERE id = ?", (old_id,)).fetchone()[0]
    _add_evidence(conn, thread, message, old_id, "superseded", observed, when, ref, None)


def _dispute(
    conn: sqlite3.Connection,
    thread: Thread,
    message: Message,
    new_id: str,
    old_id: str,
    ref: str,
    when: str | None,
) -> None:
    """Both claims stay visible, each marked disputed. Nothing here picks a winner."""
    _add_edge(conn, new_id, "CONFLICTS_WITH", old_id)
    for claim_id in (old_id, new_id):
        observed = conn.execute(
            "SELECT observed_entity FROM claim WHERE id = ?", (claim_id,)
        ).fetchone()[0]
        _add_evidence(conn, thread, message, claim_id, "disputed", observed, when, ref, message.text)


def _existing(conn: sqlite3.Connection, claim_id: str | None) -> sqlite3.Row | None:
    if not claim_id:
        return None
    return conn.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()


def _add_source(
    conn: sqlite3.Connection,
    thread: Thread,
    claim_id: str,
    advice: list[Message],
    ref: str,
    teller_key: str,
    received_at: str,
) -> None:
    role = advice[0].role
    if role is None:
        known = conn.execute(
            "SELECT role FROM source WHERE claim_id = ? AND teller_key = ? AND role IS NOT NULL",
            (claim_id, teller_key),
        ).fetchone()
        role = known["role"] if known else None
    conn.execute(
        "INSERT INTO source (id, claim_id, channel, ref, role, teller_key, excerpt, source_time_text,"
        " received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            _next_id(conn, "source", "src"),
            claim_id,
            thread.channel,
            ref,
            role,
            teller_key,
            "\n".join(m.text for m in advice),
            thread.source_time_text(),
            received_at,
        ),
    )


def _add_outcomes(
    conn: sqlite3.Connection,
    graph: Graph,
    thread: Thread,
    item: ExtractedClaim,
    claim_id: str,
    is_new: bool,
    received_at: str,
) -> None:
    kinds = {"success": "reported_success", "failure": "reported_failure"}
    observed = conn.execute(
        "SELECT observed_entity FROM claim WHERE id = ?", (claim_id,)
    ).fetchone()[0]
    for outcome in item.outcomes:
        message = thread.message(outcome.message_seq)
        # A message that gives or defends the advice is not a report of trying it. This can miss a
        # person who does both in one message, and that is the safe way to be wrong about evidence.
        if message is None or outcome.message_seq in item.advice_message_seqs:
            continue
        unit = _literal_or_none(thread, outcome.unit_id)
        unit = unit.strip().upper() if unit else None
        if unit not in graph.nodes:
            unit = observed if is_new else None
        ref = _ref(thread, [message])
        already = conn.execute(
            "SELECT 1 FROM evidence_event WHERE claim_id = ? AND type = ? AND source_ref = ?",
            (claim_id, kinds[outcome.kind], ref),
        ).fetchone()
        if not already:
            _add_evidence(
                conn,
                thread,
                message,
                claim_id,
                kinds[outcome.kind],
                unit,
                _message_time(thread, message, received_at),
                ref,
                message.text,
            )


def _store_claim(
    conn: sqlite3.Connection, graph: Graph, thread: Thread, item: ExtractedClaim, received_at: str
) -> str:
    advice = [m for m in map(thread.message, item.advice_message_seqs) if m] or [thread.messages[0]]
    ref = _ref(thread, advice)
    when = _message_time(thread, advice[0], received_at)

    existing = _existing(conn, item.same_as_existing)
    if existing:
        claim_id = existing["id"]
        _narrow_scope(conn, graph, thread, item, claim_id)
    else:
        claim_id = _new_claim(conn, graph, thread, item, received_at)
        new = _existing(conn, claim_id)
        replaced = _existing(conn, item.replaces_existing)
        # Only a replacement of the same thing on the same entity pushes the old claim aside.
        # Anything else the model calls a replacement is shown as a conflict instead.
        if (
            replaced
            and new["binding_status"] == "bound"
            and replaced["observed_entity"] == new["observed_entity"]
            and replaced["kind"] == new["kind"]
        ):
            _supersede(conn, thread, advice[0], replaced["id"], claim_id, received_at, ref, when)
        elif replaced:
            _dispute(conn, thread, advice[0], claim_id, replaced["id"], ref, when)
        opposed = _existing(conn, item.contradicts_existing)
        if opposed:
            _dispute(conn, thread, advice[0], claim_id, opposed["id"], ref, when)

    teller_key = _teller_key(claim_id, advice[0].author)
    _add_source(conn, thread, claim_id, advice, ref, teller_key, received_at)
    told_by_this_teller = conn.execute(
        "SELECT count(*) FROM source WHERE claim_id = ? AND teller_key = ?", (claim_id, teller_key)
    ).fetchone()[0]
    # One person's second account is another source, not a second telling, and a relay is neither.
    if told_by_this_teller == 1 and not item.relayed:
        observed = _existing(conn, claim_id)["observed_entity"]
        _add_evidence(conn, thread, advice[0], claim_id, "told", observed, when, ref, None)
    _add_outcomes(conn, graph, thread, item, claim_id, not existing, received_at)
    return claim_id


def _known_claims(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT id, kind, observed_entity, scope_text, claim_text FROM claim ORDER BY id"
    ).fetchall()
    return "\n".join(
        f"{r['id']} | {r['kind']} | observed on: {r['observed_entity'] or 'unknown'}"
        f" | scope: {r['scope_text'] or 'not stated'} | {r['claim_text']}"
        for r in rows
    )


def ingest_file(
    conn: sqlite3.Connection,
    graph: Graph,
    entry: dict,
    directory: Path = SOURCES_DIR,
    cache_dir: Path = extract.EXTRACTIONS_DIR,
    refresh: bool = False,
) -> list[str]:
    path = directory / entry["file"]
    thread = parse(path, entry["file"])
    procedures = "\n".join(f"{key}: {name}" for key, name in sorted(graph.procedures.items()))
    extraction, mode = extract.extract(
        thread, _known_claims(conn), procedures, cache_dir, refresh
    )
    received_at = entry["received_at"]
    claim_ids = [_store_claim(conn, graph, thread, item, received_at) for item in extraction.claims]
    for estimate in extraction.estimates:
        unit = _literal_or_none(thread, estimate.entity_id)
        unit = unit.strip().upper() if unit else None
        message = thread.message(estimate.message_seq)
        if unit in graph.nodes and message and appears_in(estimate.value_text, message.text):
            conn.execute(
                "INSERT INTO estimate (id, entity, attribute, value_text, role, source_ref,"
                " received_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    _next_id(conn, "estimate", "est"),
                    unit,
                    estimate.attribute,
                    estimate.value_text,
                    message.role,
                    _ref(thread, [message]),
                    received_at,
                ),
            )
    conn.execute(
        "INSERT INTO ingest_log (file, sha256, channel, received_at, claim_ids, mode)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            entry["file"],
            hashlib.sha256(path.read_bytes()).hexdigest(),
            thread.channel,
            received_at,
            json.dumps(claim_ids),
            mode,
        ),
    )
    return claim_ids


def _logs_up_to(path: Path, until: str | None) -> dict[str, list[dict]]:
    if not path.exists():
        return {}
    logs: dict[str, list[dict]] = {}
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        for table in ("answer_log", "gap_log"):
            logs[table] = [
                dict(row)
                for row in conn.execute(f"SELECT * FROM {table}")
                if until is None or row["asked_at"] <= until
            ]
    except sqlite3.OperationalError:
        return {}  # a store from an older schema has nothing worth carrying over
    finally:
        conn.close()
    return logs


def run(
    path: Path | None = None,
    until: str | None = None,
    replacing: dict[str, dict] | None = None,
    refresh: bool = False,
    cache_dir: Path = extract.EXTRACTIONS_DIR,
) -> Path:
    """Build the store as it stands at the demo clock. `replacing` swaps a source for a variant.

    The agent's logs are the one thing not derived from `data/`, so they carry over from the store being
    replaced, up to the clock.
    """
    logs = _logs_up_to(path or db.store_path(), until)
    path = db.build(path)
    entries = [
        (replacing or {}).get(entry["file"], entry) for entry in load_manifest()["sources"]
    ]
    entries.sort(key=lambda entry: entry["received_at"])
    with db.session(path) as conn:
        graph = Graph.load(conn)
        load_events(conn, until)
        load_telemetry(conn, until)
        for entry in entries:
            if until is None or entry["received_at"] <= until:
                ingest_file(conn, graph, entry, cache_dir=cache_dir, refresh=refresh)
        events.link_telemetry_outcomes(conn, graph)
        conn.execute("INSERT INTO meta (key, value) VALUES ('as_of', ?)", (until or "",))
        for table, rows in logs.items():
            for row in rows:
                marks = ", ".join("?" for _ in row)
                conn.execute(
                    f"INSERT INTO {table} ({', '.join(row)}) VALUES ({marks})", tuple(row.values())
                )
        events.settle_answers(conn)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the claim store from the sources.")
    parser.add_argument("--until", help="The demo clock, for example 2026-10-20T12:00:00.")
    parser.add_argument("--refresh", action="store_true", help="Ask the model again for every source.")
    parser.add_argument("--truth", action="store_true", help="Score the result against the truth set.")
    parser.add_argument(
        "--repeat-held-out",
        type=int,
        metavar="RUNS",
        help="Run the held-out set again with fresh model calls, to measure how much the result moves.",
    )
    args = parser.parse_args()
    try:
        if args.truth or args.repeat_held_out:
            from app import scoring

            if args.repeat_held_out:
                scoring.repeat_decoys(args.repeat_held_out)
            else:
                scoring.report(refresh=args.refresh)
            return
        path = run(until=args.until, refresh=args.refresh)
    except llm.ModelNotConfigured as error:
        sys.exit(str(error))
    with db.session(path) as conn:
        claims = conn.execute("SELECT count(*) FROM claim").fetchone()[0]
        sources = conn.execute("SELECT count(*) FROM ingest_log").fetchone()[0]
    print(f"{path}: {sources} sources read, {claims} claims")


if __name__ == "__main__":
    main()

"""The graph as JSON: stable ids, edge types, times and sources.

This is the bridge to another graph store. Nodes and edges map directly onto a property graph. The
teller key is left out on purpose: it exists only to merge one person's accounts, inside the store.
"""

import json
import sqlite3
from pathlib import Path

from app import db

EXPORT_FILE = db.ROOT / "export" / "graph.json"

CLAIM_FIELDS = (
    "claim_text",
    "symptom",
    "observed_entity",
    "scope_text",
    "scope_status",
    "applies_to",
    "valid_from",
    "valid_from_basis",
    "valid_to",
    "valid_to_basis",
    "received_at",
    "superseded_at",
    "binding_status",
    "binding_reason",
)


def _claim_node(conn: sqlite3.Connection, claim: sqlite3.Row) -> dict:
    sources = conn.execute(
        "SELECT channel, ref, role, source_time_text, received_at FROM source"
        " WHERE claim_id = ? ORDER BY received_at, id",
        (claim["id"],),
    ).fetchall()
    evidence = conn.execute(
        "SELECT type, scope_entity, event_time, source_ref, excerpt, basis FROM evidence_event"
        " WHERE claim_id = ? ORDER BY event_time, id",
        (claim["id"],),
    ).fetchall()
    return {
        "id": claim["id"],
        "kind": "claim",
        "claim_kind": claim["kind"],
        **{field: claim[field] for field in CLAIM_FIELDS},
        "sources": [dict(row) for row in sources],
        "evidence": [dict(row) for row in evidence],
    }


def graph(conn: sqlite3.Connection) -> dict:
    entities = conn.execute("SELECT id, kind, name, attrs FROM entity ORDER BY id").fetchall()
    claims = conn.execute("SELECT * FROM claim ORDER BY id").fetchall()
    edges = conn.execute(
        "SELECT src, rel, dst, valid_from, valid_to FROM edge ORDER BY src, rel, dst"
    ).fetchall()
    return {
        "nodes": [
            {"id": e["id"], "kind": e["kind"], "name": e["name"], "attrs": json.loads(e["attrs"])}
            for e in entities
        ]
        + [_claim_node(conn, claim) for claim in claims],
        "edges": [dict(edge) for edge in edges],
    }


def write(conn: sqlite3.Connection, path: Path = EXPORT_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph(conn), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    with db.session() as connection:
        print(write(connection))

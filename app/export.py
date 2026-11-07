"""The graph as JSON and as Cypher: stable ids, edge types, times and sources.

This is the bridge to another graph store. Nodes and edges map directly onto a property graph, and
the Cypher file loads into Neo4j as it is. The teller key is left out on purpose: it exists only to
merge one person's accounts, inside the store.
"""

import json
import sqlite3
from pathlib import Path

from app import db

EXPORT_FILE = db.ROOT / "export" / "graph.json"
CYPHER_FILE = db.ROOT / "export" / "graph.cypher"

CLAIM_FIELDS = (
    "claim_text",
    "symptom",
    "observed_entity",
    "scope_text",
    "scope_status",
    "applies_to",
    "action_kind",
    "valid_from",
    "valid_from_basis",
    "valid_to",
    "valid_to_basis",
    "received_at",
    "superseded_at",
    "binding_status",
    "binding_reason",
)

# Entity kinds as graph labels. Every entity also carries the label Entity, so one index finds any id.
LABELS = {
    "node": "Node",
    "device_class": "DeviceClass",
    "procedure_type": "ProcedureType",
    "site": "Site",
    "access_barrier": "AccessBarrier",
    "group": "Group",
}


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


# Cypher


def _literal(value) -> str:
    """A Cypher literal. Nested maps are not properties, so they become JSON text."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        return _literal(json.dumps(value, ensure_ascii=False, sort_keys=True))
    text = str(value).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return f"'{text}'"


def _props(mapping: dict) -> str:
    inside = ", ".join(f"{key}: {_literal(value)}" for key, value in mapping.items() if value is not None)
    return "{" + inside + "}"


def cypher(conn: sqlite3.Connection) -> str:
    """The same graph as Cypher statements, one per line, for `cypher-shell -f`.

    Sources and evidence events become nodes of their own, because a property cannot hold a list of
    maps. An evidence event with a unit points at that unit.
    """
    data = graph(conn)
    lines = [
        "// Silent context: the claim graph as Cypher, generated from the store. Nothing here is",
        "// original: the store is rebuilt from data/, and so is this file.",
        "// Load into an empty Neo4j 5 database with: cypher-shell -f graph.cypher",
        "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;",
        "CREATE CONSTRAINT claim_id IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE;",
    ]
    for node in data["nodes"]:
        if node["kind"] != "claim":
            props = {"id": node["id"], "name": node["name"], **node["attrs"]}
            lines.append(f"CREATE (:Entity:{LABELS[node['kind']]} {_props(props)});")
            continue
        props = {"id": node["id"], "claim_kind": node["claim_kind"]}
        props.update({field: node[field] for field in CLAIM_FIELDS})
        lines.append(f"CREATE (:Claim {_props(props)});")
        this = f"MATCH (c:Claim {{id: {_literal(node['id'])}}})"
        for source in node["sources"]:
            lines.append(f"{this} CREATE (c)-[:FROM_SOURCE]->(:Source {_props(source)});")
        for event in node["evidence"]:
            unit = event["scope_entity"]
            props = {key: value for key, value in event.items() if key != "scope_entity"}
            if unit:
                lines.append(
                    f"{this}, (u:Entity {{id: {_literal(unit)}}})"
                    f" CREATE (c)-[:HAS_EVIDENCE]->(:Evidence {_props(props)})-[:ON]->(u);"
                )
            else:
                lines.append(f"{this} CREATE (c)-[:HAS_EVIDENCE]->(:Evidence {_props(props)});")
    for edge in data["edges"]:
        props = {key: edge[key] for key in ("valid_from", "valid_to") if edge[key]}
        rel = f"[:{edge['rel']} {_props(props)}]" if props else f"[:{edge['rel']}]"
        lines.append(
            f"MATCH (a {{id: {_literal(edge['src'])}}}), (b {{id: {_literal(edge['dst'])}}})"
            f" CREATE (a)-{rel}->(b);"
        )
    return "\n".join(lines) + "\n"


def write(conn: sqlite3.Connection, path: Path = EXPORT_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph(conn), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_cypher(conn: sqlite3.Connection, path: Path = CYPHER_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cypher(conn), encoding="utf-8")
    return path


if __name__ == "__main__":
    with db.session() as connection:
        print(write(connection))
        print(write_cypher(connection))

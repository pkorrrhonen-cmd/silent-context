"""The store, the seed graph, the export and the contract of claims_for."""

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db, export
from app.api import app
from app.claims import claims_for

BOUND_CLAIM = (
    "INSERT INTO claim (id, kind, claim_text, observed_entity, received_at, binding_status)"
    " VALUES ('c1', 'troubleshooting', 'text', 'TRN-042', '2026-10-14T23:00:00', 'bound')"
)


@pytest.fixture
def conn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "store.db"
    monkeypatch.setenv("STORE_PATH", str(path))
    with db.session(path) as connection:
        yield connection


def seed_data() -> dict:
    return json.loads(db.SEED_FILE.read_text(encoding="utf-8"))


def test_seed_loads_every_entity_and_edge(conn: sqlite3.Connection) -> None:
    data = seed_data()
    assert conn.execute("SELECT count(*) FROM entity").fetchone()[0] == len(data["entities"])
    assert conn.execute("SELECT count(*) FROM edge").fetchone()[0] == len(data["edges"])
    assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 0


def test_the_seed_graph_holds_what_the_cases_need(conn: sqlite3.Connection) -> None:
    kinds = {row["kind"] for row in conn.execute("SELECT kind FROM entity")}
    assert kinds == {"node", "device_class", "procedure_type", "site", "access_barrier", "group"}
    for src, rel, dst in (
        ("TRN-042", "INSTANCE_OF", "cls-trn-gen1"),
        ("TRN-051", "INSTANCE_OF", "cls-trn-gen1"),
        ("TRN-100", "INSTANCE_OF", "cls-trn-gen2"),
        ("TRN-042", "LOCATED_AT", "SITE-NILO"),
        ("SITE-NILO", "HAS_BARRIER", "BAR-NILO-1"),
    ):
        row = conn.execute(
            "SELECT 1 FROM edge WHERE src = ? AND rel = ? AND dst = ?", (src, rel, dst)
        ).fetchone()
        assert row is not None, (src, rel, dst)


def test_class_attribute_agrees_with_the_instance_edge() -> None:
    data = seed_data()
    instance_of = {e["src"]: e["dst"] for e in data["edges"] if e["rel"] == "INSTANCE_OF"}
    nodes = [e for e in data["entities"] if e["kind"] == "node"]
    assert nodes
    for node in nodes:
        assert node["attrs"]["class_id"] == instance_of[node["id"]], node["id"]


def test_rebuild_replaces_the_store(tmp_path: Path) -> None:
    path = tmp_path / "store.db"
    with db.session(path) as conn:
        conn.execute(BOUND_CLAIM)
    db.build(path)
    with db.session(path) as conn:
        assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 0
    assert [p.name for p in tmp_path.iterdir()] == ["store.db"]


@pytest.mark.parametrize(
    "sql",
    [
        pytest.param(
            "INSERT INTO claim (id, kind, claim_text, received_at, binding_status)"
            " VALUES ('c', 'access', 't', '2026-01-01', 'waiting')",
            id="waiting-without-a-reason",
        ),
        pytest.param(
            "INSERT INTO claim (id, kind, claim_text, received_at, binding_status)"
            " VALUES ('c', 'access', 't', '2026-01-01', 'bound')",
            id="bound-without-an-entity",
        ),
        pytest.param(
            "INSERT INTO claim (id, kind, claim_text, observed_entity, received_at, binding_status,"
            " valid_from) VALUES ('c', 'access', 't', 'TRN-042', '2026-01-01', 'bound', '2026-01-01')",
            id="world-time-without-a-basis",
        ),
        pytest.param(
            "INSERT INTO claim (id, kind, claim_text, observed_entity, received_at, binding_status,"
            " valid_to, valid_to_basis) VALUES ('c', 'access', 't', 'TRN-042', '2026-01-01', 'bound',"
            " '2026-01-02', 'superseded_end_unknown')",
            id="an-end-both-known-and-unknown",
        ),
        pytest.param(
            "INSERT INTO claim (id, kind, claim_text, observed_entity, received_at, binding_status)"
            " VALUES ('c', 'access', 't', 'TRN-999', '2026-01-01', 'bound')",
            id="entity-not-in-the-graph",
        ),
        pytest.param(
            "INSERT INTO edge (src, rel, dst) VALUES ('a', 'RELATED_TO', 'b')",
            id="unknown-edge-type",
        ),
        pytest.param(
            "INSERT INTO evidence_event (id, claim_id, type, basis)"
            " VALUES ('e', 'no-such-claim', 'told', 'message')",
            id="evidence-without-a-claim",
        ),
    ],
)
def test_the_schema_refuses(conn: sqlite3.Connection, sql: str) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(sql)


def test_a_time_with_its_basis_and_an_unknown_end_are_accepted(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO claim (id, kind, claim_text, observed_entity, received_at, binding_status,"
        " valid_from, valid_from_basis, valid_to_basis) VALUES ('c', 'access', 't', 'BAR-NILO-1',"
        " '2026-09-02T23:00:00', 'bound', '2026-09-02', 'stated', 'superseded_end_unknown')"
    )


def test_claims_for_on_an_empty_store_says_it_does_not_know(conn: sqlite3.Connection) -> None:
    answer = claims_for("TRN-051", "link up, counters zero after SFP replacement", conn=conn)
    assert set(answer) == {
        "tier",
        "match_level",
        "match_note",
        "next_step",
        "action_kind",
        "prohibition",
        "claims",
        "evidence_rendered",
        "what_would_change",
        "question",
        "who_acts",
        "who_why",
        "ask_group",
        "reason_code",
        "observed_used",
        "answer_id",
    }
    assert answer["tier"] == "unknown"
    assert answer["reason_code"] == "no_claims"
    assert answer["claims"] == []
    assert answer["ask_group"] == "transmission-oncall"
    assert answer["what_would_change"]


def test_claims_for_logs_the_answer_and_the_gap(conn: sqlite3.Connection) -> None:
    answer = claims_for("TRN-051", "some symptom", conn=conn)
    logged = conn.execute("SELECT * FROM answer_log WHERE id = ?", (answer["answer_id"],)).fetchone()
    assert logged["tier"] == "unknown"
    assert json.loads(logged["claim_ids"]) == []
    gap = conn.execute("SELECT * FROM gap_log WHERE entity = 'TRN-051'").fetchone()
    assert gap["symptom"] == "some symptom"
    assert gap["ask_group"] == "transmission-oncall"


def test_claims_for_on_an_unknown_id_names_the_reason_and_a_group(conn: sqlite3.Connection) -> None:
    answer = claims_for("TRN-999", "some symptom", conn=conn)
    assert answer["tier"] == "unknown"
    assert answer["reason_code"] == "entity_unclear"
    assert answer["ask_group"] == "transmission-oncall"


def test_claims_for_without_a_connection_uses_the_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "own.db"))
    assert claims_for("TRN-051", "some symptom")["reason_code"] == "no_claims"
    with db.session() as conn:
        assert conn.execute("SELECT count(*) FROM answer_log").fetchone()[0] == 1


def test_graph_endpoint_returns_the_seed_as_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "api.db"))
    response = TestClient(app).get("/graph")
    assert response.status_code == 200
    graph = response.json()
    assert {"TRN-042", "cls-trn-gen1", "PROC-SFP-REPLACE", "BAR-NILO-1"} <= {
        node["id"] for node in graph["nodes"]
    }
    assert {"src": "TRN-051", "rel": "INSTANCE_OF", "dst": "cls-trn-gen1"}.items() <= next(
        e for e in graph["edges"] if e["src"] == "TRN-051" and e["rel"] == "INSTANCE_OF"
    ).items()


def test_export_carries_sources_but_not_the_teller_key(
    conn: sqlite3.Connection, tmp_path: Path
) -> None:
    conn.execute(BOUND_CLAIM)
    conn.execute(
        "INSERT INTO source (id, claim_id, channel, ref, role, teller_key, excerpt, received_at)"
        " VALUES ('s1', 'c1', 'teams', 'teams_trn042.json#seq=8', 'Network Expert', 'secret-teller',"
        " 'quote', '2026-10-14T23:00:00')"
    )
    conn.execute("INSERT INTO edge (src, rel, dst) VALUES ('c1', 'ABOUT', 'TRN-042')")
    path = export.write(conn, tmp_path / "out" / "graph.json")
    text = path.read_text(encoding="utf-8")
    assert "secret-teller" not in text
    assert "teller_key" not in text
    written = json.loads(text)
    claim = next(node for node in written["nodes"] if node["id"] == "c1")
    assert claim["kind"] == "claim"
    assert claim["sources"][0]["ref"] == "teams_trn042.json#seq=8"
    assert claim["sources"][0]["role"] == "Network Expert"
    assert {"src": "c1", "rel": "ABOUT", "dst": "TRN-042"}.items() <= next(
        e for e in written["edges"] if e["src"] == "c1"
    ).items()


def test_export_is_stable_between_runs(conn: sqlite3.Connection) -> None:
    assert export.graph(conn) == export.graph(conn)


def test_cypher_export_writes_every_node_and_edge_without_the_teller_key(
    conn: sqlite3.Connection, tmp_path: Path
) -> None:
    conn.execute(BOUND_CLAIM.replace("'text'", "'what''s said'"))
    conn.execute(
        "INSERT INTO source (id, claim_id, channel, ref, role, teller_key, excerpt, received_at)"
        " VALUES ('s1', 'c1', 'teams', 'teams_trn042.json#seq=8', 'Network Expert', 'secret-teller',"
        " 'quote', '2026-10-14T23:00:00')"
    )
    conn.execute(
        "INSERT INTO evidence_event (id, claim_id, scope_entity, type, event_time, basis)"
        " VALUES ('e1', 'c1', 'TRN-042', 'reported_success', '2026-10-14T09:25:00', 'message')"
    )
    conn.execute("INSERT INTO edge (src, rel, dst) VALUES ('c1', 'ABOUT', 'TRN-042')")
    text = export.write_cypher(conn, tmp_path / "out" / "graph.cypher").read_text(encoding="utf-8")
    assert "secret-teller" not in text
    assert "teller_key" not in text
    entities = conn.execute("SELECT count(*) FROM entity").fetchone()[0]
    assert text.count("CREATE (:Entity:") == entities
    assert "CREATE (:Claim {id: 'c1', claim_kind: 'troubleshooting', claim_text: 'what\\'s said'" in text
    assert "(:Source {channel: 'teams', ref: 'teams_trn042.json#seq=8', role: 'Network Expert'" in text
    assert "(u:Entity {id: 'TRN-042'}) CREATE (c)-[:HAS_EVIDENCE]->(:Evidence {" in text
    assert "-[:ON]->(u);" in text
    assert "MATCH (a {id: 'c1'}), (b {id: 'TRN-042'}) CREATE (a)-[:ABOUT]->(b);" in text
    statements = [line for line in text.splitlines() if line and not line.startswith("//")]
    assert all(line.endswith(";") for line in statements)
    assert "\n" not in text.replace("\n", "", text.count("\n"))  # no bare newline inside a literal

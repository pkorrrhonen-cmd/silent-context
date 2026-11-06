"""Extraction, binding and merging with a scripted model, so no endpoint or key is needed."""

import json
from pathlib import Path

import pytest

from app import db, ingest, llm
from app.resolve import Binding, Graph, resolve_target
from app.sources import SOURCES_DIR, appears_in, parse


def claim(**overrides) -> dict:
    base = {
        "kind": "troubleshooting",
        "claim_text": "Check the counters first.",
        "symptom": "no traffic",
        "advice_message_seqs": [1],
        "relayed": False,
        "target_node_ids": [],
        "target_sites": [],
        "target_ports": [],
        "target_firmware": None,
        "mentions_barrier": False,
        "procedure_type": None,
        "scope_text": None,
        "scope_names_version": None,
        "check_step": None,
        "check_kind": None,
        "action": None,
        "action_kind": "none",
        "do_not_before": None,
        "relative_time": None,
        "same_as_existing": None,
        "replaces_existing": None,
        "contradicts_existing": None,
        "outcomes": [],
    }
    return {**base, **overrides}


def teams(path: Path, day: str | None, *messages: tuple[str, str, str]) -> None:
    path.write_text(
        json.dumps(
            {
                "channel": "teams",
                **({"date": day} if day else {}),
                "messages": [
                    {"seq": i, "time": f"10:{i:02d}", "author": a, "role": r, "text": t}
                    for i, (a, r, t) in enumerate(messages, start=1)
                ],
            }
        ),
        encoding="utf-8",
    )


class Script:
    """Feeds the model's answers one by one and counts the calls."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.answers: list[dict] = []
        self.calls = 0
        monkeypatch.setattr(llm, "complete_json", self._complete)
        monkeypatch.setattr(llm, "model_name", lambda: "scripted")

    def _complete(self, system: str, user: str, name: str, schema: dict) -> dict:
        self.calls += 1
        return self.answers.pop(0)

    def next(self, *claims: dict, estimates: list[dict] | None = None) -> None:
        self.answers.append({"claims": list(claims), "estimates": estimates or []})


@pytest.fixture
def script(monkeypatch: pytest.MonkeyPatch) -> Script:
    return Script(monkeypatch)


@pytest.fixture
def store(tmp_path: Path):
    path = db.build(tmp_path / "store.db")
    with db.session(path) as conn:
        ingest.load_events(conn, None)
        yield conn, Graph.load(conn)


@pytest.fixture
def run_file(tmp_path: Path, store):
    conn, graph = store
    records = tmp_path / "records"

    def run(file: str, received_at: str = "2026-10-14T23:00:00") -> list[str]:
        return ingest.ingest_file(
            conn, graph, {"file": file, "received_at": received_at}, tmp_path, records
        )

    return run


# Binding


@pytest.fixture
def graph(store) -> Graph:
    return store[1]


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({"node_ids": ["TRN-042"]}, Binding("TRN-042", None)),
        ({"node_ids": ["trn-042"]}, Binding("TRN-042", None)),
        ({}, Binding(None, "no_id")),
        ({"node_ids": ["TRN-420"]}, Binding(None, "unknown_id")),
        ({"node_ids": ["TRN-042", "TRN-051"]}, Binding(None, "multiple_candidates")),
        ({"node_ids": ["TRN-042", "TRN-420"]}, Binding(None, "multiple_candidates")),
        ({"ports": ["ge-0/0/1"]}, Binding(None, "multiple_candidates")),
        ({"ports": ["xe-0/1/0"]}, Binding("TRN-100", None)),
        ({"ports": ["ge-9/9/9"]}, Binding(None, "unknown_id")),
        ({"ports": ["ge-0/0/1"], "sites": ["Rauta"]}, Binding("TRN-051", None)),
        ({"sites": ["Rauta site"]}, Binding("TRN-051", None)),
        ({"sites": ["Oulu"]}, Binding(None, "unknown_id")),
        ({"node_ids": ["TRN-042"], "sites": ["Rauta"]}, Binding(None, "contradicting_context")),
        ({"node_ids": ["TRN-042"], "firmware": "6.1"}, Binding(None, "contradicting_context")),
        ({"node_ids": ["TRN-042"], "firmware": "4.x"}, Binding("TRN-042", None)),
        ({"firmware": "4.x"}, Binding(None, "no_id")),
    ],
)
def test_resolving_a_troubleshooting_target(graph: Graph, kwargs: dict, expected: Binding) -> None:
    args = {"node_ids": [], "sites": [], "ports": [], "firmware": None, **kwargs}
    assert resolve_target(graph, "troubleshooting", mentions_barrier=False, **args) == expected


@pytest.mark.parametrize(
    "barrier, expected", [(True, Binding("BAR-NILO-1", None)), (False, Binding("SITE-NILO", None))]
)
def test_access_knowledge_belongs_to_the_place_or_its_barrier(
    graph: Graph, barrier: bool, expected: Binding
) -> None:
    assert resolve_target(graph, "access", [], ["Nilo"], [], None, barrier) == expected


def test_a_version_points_to_one_class(graph: Graph) -> None:
    assert graph.class_for_version("the 4.x firmware") == "cls-trn-gen1"
    assert graph.class_for_version("6.1") == "cls-trn-gen2"
    assert graph.class_for_version("9.x") is None
    assert graph.class_for_version("the old ones") is None


# Sources


def test_elisas_email_has_no_time_and_keeps_its_subject() -> None:
    thread = parse(SOURCES_DIR / "email_trn042.txt", "email_trn042.txt")
    assert thread.day is None and thread.source_time_text() is None
    assert "TRN-042" in thread.subject
    assert thread.messages[0].author == "Erkki Expert"
    assert "TRN-042" in thread.full_text()


def test_a_dated_email_gives_its_day_and_time() -> None:
    thread = parse(SOURCES_DIR / "email_key_moved.txt", "email_key_moved.txt")
    assert thread.day == "2026-10-20"
    assert thread.messages[0].time == "08:31"
    assert thread.source_time_text() == "Tue, 20 Oct 2026 08:31"


def test_a_teams_export_keeps_its_clock_times() -> None:
    thread = parse(SOURCES_DIR / "teams_trn042.json", "teams_trn042.json")
    assert thread.day is None
    assert thread.source_time_text() == "09:14 to 09:27"
    assert thread.message(3).text == "Yes, installed around 2019 I think."


def test_appears_in_ignores_case_and_line_breaks() -> None:
    assert appears_in("older  units", "the OLDER\nunits here")
    assert not appears_in("newer units", "the older units")
    assert not appears_in("", "anything")


# What only the text can give


def test_an_identifier_the_text_does_not_have_is_dropped(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "t.json", None, ("A", "Expert", "Check the counters first."))
    script.next(claim(target_node_ids=["TRN-042"]))
    claim_id = run_file("t.json")[0]
    row = conn.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
    assert row["binding_status"] == "waiting"
    assert row["binding_reason"] == "no_id"
    assert row["observed_entity"] is None
    assert not conn.execute("SELECT 1 FROM edge WHERE src = ?", (claim_id,)).fetchone()


def test_a_scope_the_speaker_did_not_say_is_dropped(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "t.json", None, ("A", "Expert", "On TRN-042 check the counters first."))
    script.next(claim(target_node_ids=["TRN-042"], scope_text="units installed before 2019"))
    claim_id = run_file("t.json")[0]
    row = conn.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
    assert row["scope_text"] is None and row["scope_status"] == "undefined"


def test_a_source_with_no_claim_is_logged_with_its_checksum(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "t.json", None, ("A", "Expert", "Lunch?"))
    script.next()
    assert run_file("t.json") == []
    row = conn.execute("SELECT * FROM ingest_log WHERE file = 't.json'").fetchone()
    assert len(row["sha256"]) == 64 and json.loads(row["claim_ids"]) == []
    assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 0


# Merging and evidence


def test_one_tellers_two_channels_are_one_claim_two_sources_one_telling(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "t.json", None, ("Erkki", "Network Expert", "On TRN-042 check the counters."))
    (tmp_path / "e.txt").write_text(
        "From: Erkki\nTo: V\nSubject: TRN-042\n\nCheck the counters.\n", encoding="utf-8"
    )
    script.next(claim(target_node_ids=["TRN-042"]))
    first = run_file("t.json")[0]
    script.next(claim(same_as_existing=first))
    assert run_file("e.txt") == [first]
    assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 1
    sources = conn.execute("SELECT * FROM source ORDER BY id").fetchall()
    assert [s["channel"] for s in sources] == ["teams", "email"]
    assert sources[0]["teller_key"] == sources[1]["teller_key"]
    assert sources[1]["role"] == "Network Expert"
    assert conn.execute("SELECT count(*) FROM evidence_event WHERE type = 'told'").fetchone()[0] == 1


def test_a_relay_is_a_source_but_not_a_telling(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "a.json", None, ("Erkki", "Expert", "On TRN-042 check the counters."))
    teams(tmp_path / "b.json", None, ("Pekka", "On-call", "Erkki said to check the counters."))
    script.next(claim(target_node_ids=["TRN-042"]))
    first = run_file("a.json")[0]
    script.next(claim(same_as_existing=first, relayed=True))
    run_file("b.json")
    assert conn.execute("SELECT count(*) FROM source").fetchone()[0] == 2
    assert conn.execute("SELECT count(*) FROM evidence_event WHERE type = 'told'").fetchone()[0] == 1


def test_a_teller_key_cannot_link_one_person_across_claims(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "a.json", None, ("Erkki", "Expert", "On TRN-042 check the counters."))
    teams(tmp_path / "b.json", None, ("Erkki", "Expert", "On TRN-051 clean the fan."))
    script.next(claim(target_node_ids=["TRN-042"]))
    run_file("a.json")
    script.next(claim(target_node_ids=["TRN-051"], claim_text="Clean the fan."))
    run_file("b.json")
    keys = [r["teller_key"] for r in conn.execute("SELECT teller_key FROM source")]
    assert len(set(keys)) == 2


def test_an_outcome_keeps_the_whole_message_and_names_the_unit_it_happened_on(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "a.json", None, ("Erkki", "Expert", "On TRN-042 check the counters."))
    script.next(claim(target_node_ids=["TRN-042"]))
    first = run_file("a.json")[0]
    teams(
        tmp_path / "b.json",
        "2026-10-21",
        ("Pekka", "On-call", "Try what they did on TRN-042."),
        ("Aino", "Engineer", "Done. Traffic is back on TRN-051."),
    )
    script.next(
        claim(
            same_as_existing=first,
            relayed=True,
            outcomes=[{"kind": "success", "message_seq": 2, "unit_id": "TRN-051"}],
        )
    )
    run_file("b.json")
    row = conn.execute(
        "SELECT * FROM evidence_event WHERE type = 'reported_success'"
    ).fetchone()
    assert row["scope_entity"] == "TRN-051"
    assert row["excerpt"] == "Done. Traffic is back on TRN-051."
    assert row["event_time"] == "2026-10-21T10:02:00"
    assert row["source_ref"] == "b.json#seq=2"


def test_defending_the_advice_is_not_a_report_of_trying_it(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(
        tmp_path / "t.json",
        None,
        ("Erkki", "Expert", "On TRN-042 bounce it. It was fine there last time."),
        ("Veikko", "Engineer", "Did that. Traffic is back."),
    )
    script.next(
        claim(
            target_node_ids=["TRN-042"],
            advice_message_seqs=[1],
            outcomes=[
                {"kind": "success", "message_seq": 1, "unit_id": "TRN-042"},
                {"kind": "success", "message_seq": 2, "unit_id": "TRN-042"},
            ],
        )
    )
    run_file("t.json")
    refs = [
        row["source_ref"]
        for row in conn.execute(
            "SELECT source_ref FROM evidence_event WHERE type = 'reported_success'"
        )
    ]
    assert refs == ["t.json#seq=2"]


# Time


def test_the_anchor_is_the_recent_event_not_an_old_one(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "t.json", None, ("Erkki", "Expert", "On TRN-042 check the counters."))
    script.next(claim(target_node_ids=["TRN-042"], procedure_type="PROC-SFP-REPLACE"))
    claim_id = run_file("t.json")[0]
    row = conn.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
    assert (row["valid_from"], row["valid_from_basis"]) == ("2026-10-14T09:05:00", "anchored")


def test_no_event_nearby_leaves_the_start_unknown(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "t.json", "2026-11-02", ("S", "Expert", "On TRN-051 replace the SFP first."))
    script.next(claim(target_node_ids=["TRN-051"], procedure_type="PROC-SFP-REPLACE"))
    claim_id = run_file("t.json", "2026-11-02T23:00:00")[0]
    row = conn.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()
    assert row["valid_from"] is None and row["valid_from_basis"] is None
    assert row["received_at"] == "2026-11-02T23:00:00"


def key_email(path: Path, date: str | None, body: str) -> None:
    header = f"Date: {date}\n" if date else ""
    path.write_text(f"From: H\nTo: F\n{header}Subject: Nilo\n\n{body}\n", encoding="utf-8")


def key_claim(**overrides) -> dict:
    return claim(
        kind="access",
        claim_text="The key is in the box.",
        symptom=None,
        target_sites=["Nilo"],
        mentions_barrier=True,
        **overrides,
    )


def test_a_dated_replacement_closes_the_old_claim_on_a_known_day(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    key_email(tmp_path / "a.txt", "Wed, 2 Sep 2026 14:12", "At Nilo the barrier key is in the box.")
    script.next(key_claim())
    old = run_file("a.txt", "2026-09-02T23:00:00")[0]
    key_email(tmp_path / "b.txt", "Tue, 20 Oct 2026 08:31", "At Nilo I moved the key yesterday.")
    script.next(key_claim(replaces_existing=old, relative_time="yesterday"))
    new = run_file("b.txt", "2026-10-20T23:00:00")[0]
    first = conn.execute("SELECT * FROM claim WHERE id = ?", (old,)).fetchone()
    second = conn.execute("SELECT * FROM claim WHERE id = ?", (new,)).fetchone()
    assert (first["valid_from"], first["valid_from_basis"]) == ("2026-09-02", "stated")
    assert (first["valid_to"], first["valid_to_basis"]) == ("2026-10-19", "stated")
    assert first["superseded_at"] == "2026-10-20T23:00:00"
    assert second["valid_from"] == "2026-10-19"
    assert conn.execute(
        "SELECT 1 FROM edge WHERE src = ? AND rel = 'SUPERSEDES' AND dst = ?", (new, old)
    ).fetchone()


def test_an_undated_replacement_leaves_the_end_unknown(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    key_email(tmp_path / "a.txt", "Wed, 2 Sep 2026 14:12", "At Nilo the barrier key is in the box.")
    script.next(key_claim())
    old = run_file("a.txt", "2026-09-02T23:00:00")[0]
    key_email(tmp_path / "b.txt", None, "At Nilo I moved the key yesterday.")
    script.next(key_claim(replaces_existing=old, relative_time="yesterday"))
    new = run_file("b.txt", "2026-10-20T23:00:00")[0]
    first = conn.execute("SELECT * FROM claim WHERE id = ?", (old,)).fetchone()
    second = conn.execute("SELECT * FROM claim WHERE id = ?", (new,)).fetchone()
    assert first["valid_to"] is None
    assert first["valid_to_basis"] == "superseded_end_unknown"
    assert first["superseded_at"] == "2026-10-20T23:00:00"
    assert second["valid_from"] is None


def test_a_replacement_on_another_entity_is_shown_as_a_conflict(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    key_email(tmp_path / "a.txt", "Wed, 2 Sep 2026 14:12", "At Nilo the barrier key is in the box.")
    script.next(key_claim())
    old = run_file("a.txt", "2026-09-02T23:00:00")[0]
    teams(tmp_path / "b.json", "2026-10-20", ("H", "Tech", "On TRN-051 the fan is new."))
    script.next(claim(target_node_ids=["TRN-051"], replaces_existing=old))
    new = run_file("b.json", "2026-10-20T23:00:00")[0]
    assert conn.execute("SELECT superseded_at FROM claim WHERE id = ?", (old,)).fetchone()[0] is None
    assert conn.execute(
        "SELECT 1 FROM edge WHERE src = ? AND rel = 'CONFLICTS_WITH' AND dst = ?", (new, old)
    ).fetchone()


# Disagreement and scope


def test_opposing_advice_keeps_both_and_marks_both_disputed(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "a.json", None, ("Erkki", "Expert", "On TRN-042 bounce the interface."))
    script.next(claim(target_node_ids=["TRN-042"]))
    first = run_file("a.json")[0]
    teams(
        tmp_path / "b.json",
        "2026-11-02",
        ("Sirpa", "Expert", "On TRN-051 replace the SFP first."),
        ("Erkki", "Expert", "I stand by what I said."),
    )
    script.next(
        claim(target_node_ids=["TRN-051"], contradicts_existing=first, claim_text="Replace first."),
        claim(same_as_existing=first, advice_message_seqs=[2]),
    )
    second = run_file("b.json", "2026-11-02T23:00:00")[0]
    assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 2
    assert conn.execute(
        "SELECT 1 FROM edge WHERE src = ? AND rel = 'CONFLICTS_WITH' AND dst = ?", (second, first)
    ).fetchone()
    disputed = {
        r["claim_id"] for r in conn.execute("SELECT claim_id FROM evidence_event WHERE type = 'disputed'")
    }
    assert disputed == {first, second}
    told_first = conn.execute(
        "SELECT count(*) FROM evidence_event WHERE type = 'told' AND claim_id = ?", (first,)
    ).fetchone()[0]
    assert told_first == 1


def test_a_named_version_narrows_the_scope_and_keeps_the_earlier_words(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(tmp_path / "a.json", None, ("Erkki", "Expert", "On TRN-042 and other older units, bounce."))
    script.next(claim(target_node_ids=["TRN-042"], scope_text="older units"))
    first = run_file("a.json")[0]
    row = conn.execute("SELECT * FROM claim WHERE id = ?", (first,)).fetchone()
    assert (row["scope_status"], row["applies_to"]) == ("undefined", None)
    teams(tmp_path / "b.json", None, ("Erkki", "Expert", "That was about the 4.x firmware ones."))
    script.next(
        claim(same_as_existing=first, scope_text="the 4.x firmware ones", scope_names_version="4.x")
    )
    run_file("b.json")
    row = conn.execute("SELECT * FROM claim WHERE id = ?", (first,)).fetchone()
    assert row["scope_text"] == "older units; the 4.x firmware ones"
    assert (row["scope_status"], row["applies_to"]) == ("confirmed", "cls-trn-gen1")
    assert conn.execute(
        "SELECT 1 FROM edge WHERE src = ? AND rel = 'APPLIES_TO' AND dst = 'cls-trn-gen1'", (first,)
    ).fetchone()


# Estimates


def test_an_estimate_stays_an_estimate_with_its_source(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, _ = store
    teams(
        tmp_path / "t.json",
        None,
        ("Erkki", "Expert", "On TRN-042 check the counters."),
        ("Veikko", "Field Engineer", "Yes, installed around 2019 I think."),
    )
    script.next(
        claim(target_node_ids=["TRN-042"]),
        estimates=[
            {
                "entity_id": "TRN-042",
                "attribute": "installed_year",
                "value_text": "around 2019",
                "message_seq": 2,
            }
        ],
    )
    run_file("t.json")
    row = conn.execute("SELECT * FROM estimate").fetchone()
    assert (row["entity"], row["value_text"], row["role"]) == (
        "TRN-042",
        "around 2019",
        "Field Engineer",
    )
    assert row["source_ref"] == "t.json#seq=2"
    node = conn.execute("SELECT attrs FROM entity WHERE id = 'TRN-042'").fetchone()
    assert "installed" not in node["attrs"]


# The record


def test_a_recorded_answer_needs_no_model(
    tmp_path: Path, script: Script, run_file, store
) -> None:
    conn, graph = store
    teams(tmp_path / "t.json", None, ("Erkki", "Expert", "On TRN-042 check the counters."))
    script.next(claim(target_node_ids=["TRN-042"]))
    run_file("t.json")
    assert script.calls == 1
    log = conn.execute("SELECT mode FROM ingest_log").fetchone()
    assert log["mode"] == "model"

    second = tmp_path / "second.db"
    db.build(second)
    with db.session(second) as other:
        ingest.ingest_file(
            other,
            Graph.load(other),
            {"file": "t.json", "received_at": "2026-10-14T23:00:00"},
            tmp_path,
            tmp_path / "records",
        )
        assert other.execute("SELECT mode FROM ingest_log").fetchone()["mode"] == "recorded"
    assert script.calls == 1


def test_without_a_model_or_a_record_ingest_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_file
) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    teams(tmp_path / "t.json", None, ("Erkki", "Expert", "On TRN-042 check the counters."))
    with pytest.raises(llm.ModelNotConfigured, match="LLM_API_KEY"):
        run_file("t.json")

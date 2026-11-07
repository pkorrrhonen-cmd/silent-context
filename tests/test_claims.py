"""The agent's answers on the recorded data: the acceptance cases of the build plan."""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db, ingest
from app.api import app
from app.claims import PROHIBITION, access_for, claims_for, symptom_matches
from app.sources import load_manifest

SYMPTOM = "link up, counters zero after SFP replacement"
BEFORE_CAPTURE = "2026-10-14T22:00:00"
AFTER_CAPTURE = "2026-10-20T12:00:00"
KEY_MOVED = "2026-10-21T00:00:00"
DURING_FAULT = "2026-10-21T10:50:00"
AFTER_FIRMWARE = "2026-10-29T00:00:00"
AFTER_FAILURE = "2026-10-31T00:00:00"
AFTER_DISPUTE = "2026-11-03T00:00:00"


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory):
    root = tmp_path_factory.mktemp("clocks")
    stores: dict[str, Path] = {}

    def at_clock(clock: str) -> Path:
        if clock not in stores:
            stores[clock] = ingest.run(root / f"{len(stores)}.db", until=clock)
        return stores[clock]

    return at_clock


@pytest.fixture
def clock(built):
    """A connection to the store as it stands at a clock value."""
    sessions = []

    def open_at(value: str):
        session = db.session(built(value))
        conn = session.__enter__()
        sessions.append(session)
        return conn

    yield open_at
    for session in sessions:
        session.__exit__(None, None, None)


def erkki(answer: dict) -> dict:
    return next(c for c in answer["claims"] if c["observed_entity"] == "TRN-042")


# The acceptance cases


def test_before_capture_the_agent_does_not_know(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, conn=clock(BEFORE_CAPTURE))
    assert answer["tier"] == "unknown"
    assert answer["reason_code"] == "no_claims"
    assert answer["ask_group"] == "transmission-oncall"


def test_a1_without_counters_it_checks_first(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, conn=clock(AFTER_CAPTURE))
    assert answer["tier"] == "check_first"
    assert answer["match_level"] == "same_class"
    assert answer["action_kind"] == "read"
    assert "counter" in answer["next_step"].casefold()
    assert answer["prohibition"] == PROHIBITION
    assert "inference" in answer["match_note"]
    assert answer["ask_group"] is None


def test_a1_with_zero_counters_it_proposes_the_bounce(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_CAPTURE))
    assert answer["tier"] == "propose"
    assert answer["match_level"] == "same_class"
    assert answer["action_kind"] == "bounce_interface"
    assert "disable" in answer["next_step"].casefold()
    assert answer["prohibition"] == PROHIBITION
    claim = erkki(answer)
    assert claim["scope_status"] == "undefined"
    assert {s["channel"] for s in claim["sources"]} == {"teams", "email"}


def test_the_agent_reads_the_counters_itself_when_it_can(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, conn=clock(DURING_FAULT))
    assert answer["observed_used"] == {"counters": "zero", "counters_from": "telemetry"}
    assert answer["tier"] == "propose"


def test_old_telemetry_is_not_read_as_the_present(clock) -> None:
    answer = claims_for("TRN-042", SYMPTOM, conn=clock(AFTER_CAPTURE))
    assert answer["observed_used"] == {"counters": "unknown", "counters_from": None}
    assert answer["tier"] == "check_first"


def test_rising_counters_mean_the_advice_does_not_fit(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, observed={"counters": "rising"}, conn=clock(AFTER_CAPTURE))
    assert answer["tier"] == "unknown"
    assert answer["reason_code"] == "not_applicable"
    assert answer["ask_group"] == "transmission-oncall"


def test_a2_before_anyone_narrows_it_another_generation_is_named_a_guess(clock) -> None:
    answer = claims_for("TRN-100", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_CAPTURE))
    assert answer["match_level"] == "similar_guess"
    assert answer["tier"] == "check_first"
    assert answer["action_kind"] == "read"
    assert answer["match_note"].startswith("A guess")


def test_a2_a_guess_does_not_promise_that_counters_would_make_it_a_proposal(clock) -> None:
    answer = claims_for("TRN-100", SYMPTOM, conn=clock(AFTER_CAPTURE))
    assert answer["tier"] == "check_first"
    assert "proposal" not in answer["what_would_change"]


def test_a2_after_the_failure_the_advice_is_not_offered_for_that_generation(clock) -> None:
    answer = claims_for("TRN-100", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_FAILURE))
    assert answer["tier"] != "propose"
    assert answer["action_kind"] != "bounce_interface"
    claim = erkki(answer)
    assert claim["status_for_entity"] == "not_applicable"
    assert claim["match_level"] == "none"
    assert "4.x firmware" in claim["match_note"]
    assert any(e["type"] == "reported_failure" and e["scope"] == "TRN-100" for e in claim["evidence"])


def test_a2_the_older_generation_still_gets_the_advice_after_it_is_narrowed(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_FAILURE))
    assert answer["tier"] == "propose"
    assert answer["match_level"] == "same_class"
    assert "inference" not in answer["match_note"]
    assert "4.x firmware" in answer["match_note"]


def test_a3_a_different_symptom_is_a_gap_with_a_group(clock) -> None:
    conn = clock(AFTER_CAPTURE)
    answer = claims_for("TRN-051", "intermittent CRC errors on uplink", conn=conn)
    assert answer["tier"] == "unknown"
    assert answer["reason_code"] == "no_claims"
    assert answer["ask_group"] == "transmission-oncall"
    assert answer["claims"] == []
    gap = conn.execute(
        "SELECT * FROM gap_log WHERE symptom = 'intermittent CRC errors on uplink'"
    ).fetchone()
    assert gap["ask_group"] == "transmission-oncall"
    assert gap["asked_at"] == AFTER_CAPTURE


def test_a4_the_key_before_the_move(clock) -> None:
    answer = access_for("SITE-NILO", conn=clock(AFTER_CAPTURE))
    assert answer["tier"] == "propose"
    assert "grey box" in answer["next_step"]
    assert answer["claims"][0]["info_age_days"] == 47
    assert "Information age: 47 days" in answer["evidence_rendered"]


def test_a4_the_key_after_the_move(clock) -> None:
    answer = access_for("SITE-NILO", conn=clock(KEY_MOVED))
    assert "maintenance hut" in answer["next_step"]
    assert answer["boundary_known"] is True
    assert [c["status_for_entity"] for c in answer["claims"]] == ["active", "superseded"]
    assert answer["claims"][1]["valid_to"] == "2026-10-19"


def test_a4_a_node_counts_as_its_site(clock) -> None:
    assert "maintenance hut" in access_for("TRN-042", conn=clock(KEY_MOVED))["next_step"]


def test_a4_a_point_in_world_time_gives_the_old_key(clock) -> None:
    answer = access_for("SITE-NILO", at="2026-10-10", conn=clock(KEY_MOVED))
    assert "grey box" in answer["next_step"]
    assert answer["boundary_known"] is True
    assert "maintenance hut" not in answer["evidence_rendered"]


def test_a4_an_undated_move_gives_both_and_says_the_boundary_is_unknown(tmp_path: Path) -> None:
    variant = load_manifest()["variants"][0]
    path = ingest.run(
        tmp_path / "variant.db",
        until=variant["received_at"],
        replacing={variant["replaces"]: variant},
    )
    with db.session(path) as conn:
        answer = access_for("SITE-NILO", at="2026-10-10", conn=conn)
        assert answer["boundary_known"] is False
        assert "not known" in answer["next_step"]
        assert len([c for c in answer["claims"] if c["status_for_entity"] == "active"]) == 2
        current = access_for("SITE-NILO", conn=conn)
        assert "maintenance hut" in current["next_step"]
        assert current["claims"][1]["valid_to_basis"] == "superseded_end_unknown"


def test_a5_a_firmware_update_rechecks_that_unit_only(clock) -> None:
    conn = clock(AFTER_FIRMWARE)
    updated = claims_for("TRN-042", SYMPTOM, observed={"counters": "zero"}, conn=conn)
    assert updated["tier"] == "check_first"
    assert updated["action_kind"] == "read"
    claim = erkki(updated)
    assert claim["status_for_entity"] == "recheck"
    assert "4.8" in claim["status_note"] and "4.9" in claim["status_note"]
    assert "4.9" in updated["next_step"]
    assert "TRN-042" in updated["what_would_change"]

    same_class = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=conn)
    assert same_class["tier"] == "propose"
    assert erkki(same_class)["status_for_entity"] == "active"


def test_a5_before_the_update_nothing_is_in_doubt(clock) -> None:
    answer = claims_for("TRN-042", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_CAPTURE))
    assert answer["tier"] == "propose"
    assert erkki(answer)["status_for_entity"] == "active"


def test_a5_a_point_in_time_before_the_update_is_not_in_doubt(clock) -> None:
    answer = claims_for(
        "TRN-042",
        SYMPTOM,
        at="2026-10-20T00:00:00",
        observed={"counters": "zero"},
        conn=clock(AFTER_FIRMWARE),
    )
    assert erkki(answer)["status_for_entity"] == "active"


def test_a6_one_tellers_two_channels_show_as_one_telling(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_CAPTURE))
    rendered = erkki(answer)["evidence_rendered"]
    told = [line for line in rendered.splitlines() if line.startswith("Told:")]
    assert len(told) == 1
    assert "teams/Network Expert" in told[0] and "email/Network Expert" in told[0]
    assert not re.search(r"\b(two|twice|several|independent)\b", answer["evidence_rendered"], re.I)


@pytest.mark.parametrize("clock_value", [AFTER_CAPTURE, AFTER_FAILURE, AFTER_DISPUTE])
def test_a6_no_count_reaches_the_rendered_evidence_at_any_time(clock, clock_value: str) -> None:
    answer = claims_for("TRN-042", SYMPTOM, conn=clock(clock_value))
    rendered = answer["evidence_rendered"]
    assert rendered
    assert not re.search(r"\b(two|twice|several|independent|percent)\b|%", rendered, re.I)


def test_a7_a_disagreement_shows_both_and_the_agent_does_not_choose(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_DISPUTE))
    assert answer["tier"] == "check_first"
    assert answer["action_kind"] == "read"
    assert "does not choose" in answer["next_step"]
    assert erkki(answer)["status_for_entity"] == "disputed"
    other = next(c for c in answer["claims"] if c["binding_status"] == "waiting")
    assert other["status_for_entity"] == "disputed"
    assert "not offered as advice" in other["match_note"]
    assert answer["claims"][0]["id"] != other["id"]


def test_a7_a_question_only_a_waiting_claim_answers_gets_i_dont_know(clock) -> None:
    answer = claims_for("TRN-051", "the cage is bad on old units", conn=clock(AFTER_DISPUTE))
    assert answer["tier"] == "unknown"
    assert answer["claims"] == []


def test_a8_no_report_keeps_reboot_and_replacement_held_back(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, conn=clock(AFTER_CAPTURE))
    assert answer["action_kind"] not in ("reboot", "replace_hw")
    assert answer["prohibition"] == PROHIBITION


def test_a8_a_bounce_with_no_result_keeps_them_held_back(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, observed={"bounce_done": True}, conn=clock(AFTER_CAPTURE))
    assert answer["action_kind"] == "read"
    assert answer["prohibition"] == PROHIBITION


def test_a8_a_failed_bounce_allows_them_as_a_proposal(clock) -> None:
    answer = claims_for(
        "TRN-051",
        SYMPTOM,
        observed={"counters": "zero", "bounce_done": True, "bounce_failed": True},
        conn=clock(AFTER_CAPTURE),
    )
    assert answer["tier"] == "propose"
    assert answer["action_kind"] == "reboot"
    assert answer["prohibition"] is None


def test_a_bounce_that_worked_asks_nothing_more(clock) -> None:
    answer = claims_for(
        "TRN-051",
        SYMPTOM,
        observed={"counters": "rising", "bounce_done": True},
        conn=clock(AFTER_CAPTURE),
    )
    assert answer["action_kind"] == "none"
    assert "rising" in answer["next_step"]


# What devices add


def telemetry_events(answer: dict) -> list[dict]:
    return [e for e in erkki(answer)["evidence"] if e["basis"] == "telemetry"]


def test_a_rise_after_the_bounce_shows_apart_from_what_people_said(clock) -> None:
    answer = claims_for("TRN-042", SYMPTOM, conn=clock(AFTER_CAPTURE))
    events = telemetry_events(answer)
    assert [e["scope"] for e in events] == ["TRN-042"]
    assert events[0]["event_time"] == "2026-10-14T09:25:00"
    assert "not its cause" in events[0]["excerpt"]
    rendered = erkki(answer)["evidence_rendered"]
    assert "Observed: 2026-10-14T09:25:00 · counters rising" in rendered
    assert "suggestion" in rendered


def test_a_rise_that_followed_another_change_is_not_credited_to_the_advice(clock) -> None:
    conn = clock(AFTER_FAILURE)
    rows = conn.execute(
        "SELECT scope_entity FROM evidence_event WHERE basis = 'telemetry' ORDER BY event_time"
    ).fetchall()
    assert [row["scope_entity"] for row in rows] == ["TRN-042", "TRN-051", "TRN-063"]


def test_telemetry_alone_does_not_make_a_proposal(plain) -> None:
    add_claim(plain, "c1", action="Disable and enable it", action_kind="bounce_interface")
    plain.execute(
        "INSERT INTO evidence_event (id, claim_id, scope_entity, type, basis)"
        " VALUES ('e1', 'c1', 'TRN-051', 'reported_success', 'telemetry')"
    )
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["tier"] == "check_first"
    assert "only been told" in answer["next_step"]


def test_a_rise_does_not_set_last_confirmed(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, conn=clock(DURING_FAULT))
    assert "last confirmed 2026-10-14T09:25:00" in erkki(answer)["evidence_rendered"]


def test_what_a_person_did_comes_from_the_devices(tmp_path: Path) -> None:
    path = tmp_path / "log.db"
    ingest.run(path, until=DURING_FAULT)
    with db.session(path) as conn:
        answer = claims_for("TRN-051", SYMPTOM, conn=conn)
        row = conn.execute(
            "SELECT * FROM answer_log WHERE id = ?", (answer["answer_id"],)
        ).fetchone()
        assert row["human_did"] is None
    ingest.run(path, until="2026-10-21T11:15:00")
    with db.session(path) as conn:
        row = conn.execute(
            "SELECT * FROM answer_log WHERE id = ?", (answer["answer_id"],)
        ).fetchone()
    assert "Disable" in row["next_step"]
    assert "ge-0/0/1" in row["human_did"] and "10:53" in row["human_did"]
    assert row["outcome"] == "Counters rising afterwards"


def test_logs_do_not_survive_going_back_before_they_were_written(tmp_path: Path) -> None:
    path = tmp_path / "log.db"
    ingest.run(path, until=DURING_FAULT)
    with db.session(path) as conn:
        claims_for("TRN-051", SYMPTOM, conn=conn)
    ingest.run(path, until=AFTER_CAPTURE)
    with db.session(path) as conn:
        assert conn.execute("SELECT count(*) FROM answer_log").fetchone()[0] == 0


# Rules with data shaped for them


def add_claim(conn, claim_id: str, **fields) -> None:
    values = {
        "id": claim_id,
        "kind": "troubleshooting",
        "claim_text": "Power cycle the fan tray when it hums.",
        "symptom": "fan tray humming loudly",
        "observed_entity": "TRN-051",
        "received_at": "2026-10-01T23:00:00",
        "binding_status": "bound",
        "action": "Reboot the unit",
        "action_kind": "reboot",
        **fields,
    }
    marks = ", ".join("?" for _ in values)
    conn.execute(
        f"INSERT INTO claim ({', '.join(values)}) VALUES ({marks})", tuple(values.values())
    )


def add_outcome(conn, claim_id: str, kind: str, unit: str) -> None:
    conn.execute(
        "INSERT INTO evidence_event (id, claim_id, scope_entity, type, basis)"
        " VALUES (?, ?, ?, ?, 'message')",
        (f"e-{claim_id}-{kind}-{unit}", claim_id, unit, kind),
    )


@pytest.fixture
def plain(tmp_path: Path):
    path = db.build(tmp_path / "plain.db")
    with db.session(path) as conn:
        conn.execute("INSERT INTO meta (key, value) VALUES ('as_of', '2026-10-20T12:00:00')")
        yield conn


def add_firmware_update(conn, unit: str, when: str) -> None:
    conn.execute(
        "INSERT INTO event (id, type, entity, event_time, attrs) VALUES"
        " (?, 'firmware_updated', ?, ?, '{\"from\": \"4.8\", \"to\": \"4.9\"}')",
        (f"fw-{unit}", unit, when),
    )


def sfp_claim(conn, claim_id: str, **fields) -> None:
    add_claim(
        conn,
        claim_id,
        action="Disable and enable it",
        action_kind="bounce_interface",
        **fields,
    )
    conn.execute(
        "INSERT INTO edge (src, rel, dst) VALUES (?, 'ABOUT', 'PROC-SFP-REPLACE')", (claim_id,)
    )


def test_an_update_before_advice_with_a_known_start_raises_no_doubt(plain) -> None:
    sfp_claim(plain, "c1", valid_from="2026-10-05T00:00:00", valid_from_basis="anchored")
    add_firmware_update(plain, "TRN-051", "2026-10-02T00:00:00")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["claims"][0]["status_for_entity"] == "active"


def test_when_the_order_cannot_be_told_the_agent_says_so(plain) -> None:
    sfp_claim(plain, "c1")
    add_firmware_update(plain, "TRN-051", "2026-09-20T00:00:00")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["claims"][0]["status_for_entity"] == "order_unknown"
    assert answer["tier"] == "check_first"
    assert "not known whether" in answer["next_step"]


def test_an_update_after_the_information_arrived_is_a_recheck_even_with_no_start(plain) -> None:
    sfp_claim(plain, "c1")
    add_firmware_update(plain, "TRN-051", "2026-10-10T00:00:00")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["claims"][0]["status_for_entity"] == "recheck"


def test_a_success_reported_after_the_update_clears_the_recheck(plain) -> None:
    sfp_claim(plain, "c1")
    add_firmware_update(plain, "TRN-051", "2026-10-10T00:00:00")
    plain.execute(
        "INSERT INTO evidence_event (id, claim_id, scope_entity, type, event_time, basis)"
        " VALUES ('e1', 'c1', 'TRN-051', 'reported_success', '2026-10-12T00:00:00', 'message')"
    )
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["claims"][0]["status_for_entity"] == "active"
    assert answer["tier"] == "propose"


def test_the_recheck_rule_reads_only_firmware_and_only_this_kind_of_advice(plain) -> None:
    add_claim(plain, "c1", action="Disable and enable it", action_kind="bounce_interface")
    add_firmware_update(plain, "TRN-051", "2026-10-10T00:00:00")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["claims"][0]["status_for_entity"] == "active"


def test_the_prohibition_holds_even_when_a_claim_advises_a_reboot(plain) -> None:
    add_claim(plain, "c1")
    add_outcome(plain, "c1", "reported_success", "TRN-051")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["tier"] == "check_first"
    assert answer["action_kind"] == "read"
    assert answer["prohibition"] == PROHIBITION


def test_only_told_is_not_enough_to_propose(plain) -> None:
    add_claim(plain, "c1", action="Disable and enable it", action_kind="bounce_interface")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["tier"] == "check_first"
    assert "only been told" in answer["next_step"]


def test_a_reported_success_on_the_class_is_enough_to_propose(plain) -> None:
    add_claim(plain, "c1", action="Disable and enable it", action_kind="bounce_interface")
    add_outcome(plain, "c1", "reported_success", "TRN-042")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["tier"] == "propose"
    assert answer["action_kind"] == "bounce_interface"


def test_a_success_on_another_class_does_not_count(plain) -> None:
    add_claim(plain, "c1", action="Disable and enable it", action_kind="bounce_interface")
    add_outcome(plain, "c1", "reported_success", "TRN-100")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["tier"] == "check_first"


def test_a_failure_on_the_class_holds_a_proposal_back(plain) -> None:
    add_claim(plain, "c1", action="Disable and enable it", action_kind="bounce_interface")
    add_outcome(plain, "c1", "reported_success", "TRN-042")
    add_outcome(plain, "c1", "reported_failure", "TRN-051")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["tier"] == "check_first"
    assert "failure is reported" in answer["next_step"]


def test_a_superseded_claim_is_not_offered(plain) -> None:
    add_claim(plain, "c1", superseded_at="2026-10-02T23:00:00")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    assert answer["tier"] == "unknown"
    assert answer["reason_code"] == "superseded"
    assert answer["claims"][0]["status_for_entity"] == "superseded"


def test_a_claim_that_has_not_started_is_not_used_for_an_earlier_time(plain) -> None:
    add_claim(plain, "c1", valid_from="2026-10-10", valid_from_basis="stated")
    answer = claims_for("TRN-051", "fan tray humming", at="2026-10-01", conn=plain)
    assert answer["reason_code"] == "no_claims"


def test_an_unknown_unit_is_a_named_reason(plain) -> None:
    answer = claims_for("TRN-999", "fan tray humming", conn=plain)
    assert answer["reason_code"] == "entity_unclear"
    assert answer["ask_group"] == "transmission-oncall"


def test_access_with_no_knowledge_names_the_place_group(plain) -> None:
    answer = access_for("SITE-RAUTA", conn=plain)
    assert answer["tier"] == "unknown"
    assert answer["ask_group"] == "field-central"
    assert plain.execute("SELECT count(*) FROM gap_log").fetchone()[0] == 1


def test_access_to_an_unknown_place_is_a_named_reason(plain) -> None:
    assert access_for("SITE-NOWHERE", conn=plain)["reason_code"] == "entity_unclear"


def test_every_answer_logs_the_claims_it_used(plain) -> None:
    add_claim(plain, "c1", action="Disable and enable it", action_kind="bounce_interface")
    answer = claims_for("TRN-051", "fan tray humming", conn=plain)
    row = plain.execute("SELECT * FROM answer_log WHERE id = ?", (answer["answer_id"],)).fetchone()
    assert row["claim_ids"] == '["c1"]'
    assert row["tier"] == answer["tier"]
    assert row["asked_at"] == "2026-10-20T12:00:00"


def test_no_person_is_named_in_what_the_agent_gets(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=clock(AFTER_DISPUTE))
    claims_only = str([{k: v for k, v in c.items() if k != "claim_text"} for c in answer["claims"]])
    assert "teller_key" not in str(answer)
    for name in ("Veikko", "Vikkelä", "Sirpa Specialist", "Erkki Expert", "Aino", "Pekka"):
        assert name not in answer["evidence_rendered"], name
        assert name not in str([c["sources"] for c in answer["claims"]]), name
    assert "Expert" in claims_only


# Matching


@pytest.mark.parametrize(
    "query, text, expected",
    [
        ("link up, counters zero", "the link is up and the counters stay at zero", True),
        ("intermittent CRC errors on uplink", "the link is up and the counters stay at zero", False),
        ("no traffic after SFP replacement", "traffic does not come back", True),
        ("after SFP replacement", "traffic does not come back after SFP replacement", False),
        ("", "anything", False),
        ("counters", "", False),
    ],
)
def test_matching_a_symptom(query: str, text: str, expected: bool) -> None:
    assert symptom_matches(query, text) is expected


# Over HTTP


def test_the_answers_over_http(built, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORE_PATH", str(built(AFTER_CAPTURE)))
    client = TestClient(app)
    response = client.post(
        "/claims_for",
        json={"entity": "TRN-051", "symptom": SYMPTOM, "observed": {"counters": "zero"}},
    )
    assert response.status_code == 200
    assert response.json()["tier"] == "propose"
    assert client.post("/claims_for", json={"entity": "TRN-051"}).status_code == 422
    access = client.get("/access_for", params={"place": "SITE-NILO"})
    assert "grey box" in access.json()["next_step"]


# Who acts: the policy over the answer

AFTER_RECORD = "2026-10-25T09:40:00"
AFTER_AGENT_ACTED = "2026-10-25T09:50:00"


def test_the_first_time_the_policy_keeps_the_step_with_a_person(clock) -> None:
    answer = claims_for("TRN-051", SYMPTOM, conn=clock(DURING_FAULT))
    assert answer["tier"] == "propose"
    assert answer["who_acts"] == "person"
    assert "no proposal of this step on this class" in answer["who_why"]


def test_the_policy_lets_the_agent_act_once_its_own_log_shows_a_carried_out_success(tmp_path: Path) -> None:
    path = tmp_path / "policy.db"
    ingest.run(path, until=DURING_FAULT)
    with db.session(path) as conn:
        claims_for("TRN-051", SYMPTOM, conn=conn)
    ingest.run(path, until=AFTER_RECORD)
    with db.session(path) as conn:
        answer = claims_for("TRN-063", SYMPTOM, conn=conn)
    assert answer["tier"] == "propose"
    assert answer["observed_used"] == {"counters": "zero", "counters_from": "telemetry"}
    assert answer["who_acts"] == "agent"
    assert "TRN-051" in answer["who_why"] and "21.10." in answer["who_why"]
    # The record of the agent's own action comes from the devices, marked as the agent's.
    ingest.run(path, until=AFTER_AGENT_ACTED)
    with db.session(path) as conn:
        row = conn.execute(
            "SELECT * FROM answer_log WHERE id = ?", (answer["answer_id"],)
        ).fetchone()
    assert row["done_by"] == "agent"
    assert "09:42" in row["human_did"]
    assert row["outcome"] == "Counters rising afterwards"


def test_without_a_carried_out_success_the_third_unit_stays_with_a_person(clock) -> None:
    answer = claims_for("TRN-063", SYMPTOM, conn=clock(AFTER_RECORD))
    assert answer["tier"] == "propose"
    assert answer["who_acts"] == "person"


def test_counters_a_person_reported_do_not_let_the_agent_act(tmp_path: Path) -> None:
    path = tmp_path / "policy.db"
    ingest.run(path, until=DURING_FAULT)
    with db.session(path) as conn:
        claims_for("TRN-051", SYMPTOM, conn=conn)
    ingest.run(path, until=AFTER_RECORD)
    with db.session(path) as conn:
        answer = claims_for("TRN-063", SYMPTOM, observed={"counters": "zero"}, conn=conn)
    assert answer["who_acts"] == "person"
    assert "reported by a person" in answer["who_why"]


def test_the_policy_never_gives_a_reboot_or_a_replacement_to_the_agent(plain) -> None:
    from app import policy
    from app.resolve import Graph

    graph = Graph.load(plain)
    for kind in ("reboot", "replace_hw"):
        who = policy.who_acts(
            plain, graph, {"tier": "propose", "action_kind": kind}, "TRN-051", "telemetry"
        )
        assert who["who"] == "person"
        assert "not reversible" in who["why"]
    assert policy.who_acts(plain, graph, {"tier": "unknown", "action_kind": "none"}, "TRN-051", None)["who"] == "ask"
    assert policy.who_acts(plain, graph, {"tier": "check_first", "action_kind": "read"}, "TRN-051", None)["who"] == "person"

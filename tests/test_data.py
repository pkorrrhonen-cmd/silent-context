"""The data set's own acceptance: every source has a truth row, and every reference resolves."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "data"
SOURCES = DATA / "sources"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest() -> dict:
    return load(SOURCES / "manifest.json")


@pytest.fixture(scope="module")
def truth() -> dict:
    return load(DATA / "truth" / "expected_claims.json")


@pytest.fixture(scope="module")
def entity_ids() -> set[str]:
    return {e["id"] for e in load(DATA / "seed" / "entities.json")["entities"]}


@pytest.fixture(scope="module")
def events() -> list[dict]:
    return load(DATA / "events" / "events.json")["events"]


def test_manifest_lists_every_source_file(manifest: dict) -> None:
    on_disk = {
        p.name for p in SOURCES.iterdir() if p.is_file() and p.name != "manifest.json"
    }
    assert on_disk == {s["file"] for s in manifest["sources"]}
    for variant in manifest["variants"]:
        assert (SOURCES / variant["file"]).is_file()


def test_elisas_files_are_unchanged(manifest: dict) -> None:
    originals = [s for s in manifest["sources"] if s["origin"] == "elisa"]
    assert len(originals) == 2
    for source in originals:
        digest = hashlib.sha256((SOURCES / source["file"]).read_bytes()).hexdigest()
        assert digest == source["sha256"], source["file"]


def test_every_source_has_a_received_at(manifest: dict) -> None:
    for source in manifest["sources"] + manifest["variants"]:
        datetime.fromisoformat(source["received_at"])


def test_every_source_has_exactly_one_truth_row(manifest: dict, truth: dict) -> None:
    in_manifest = sorted(s["file"] for s in manifest["sources"])
    in_truth = sorted(row["file"] for row in truth["sources"])
    assert in_manifest == in_truth
    assert sorted(v["file"] for v in manifest["variants"]) == sorted(
        v["file"] for v in truth["variants"]
    )


def test_truth_rows_name_known_claims(truth: dict) -> None:
    for row in truth["sources"] + truth["variants"]:
        if row["has_claim"]:
            assert row["claim"] in truth["claims"], row["file"]
        else:
            assert "claim" not in row, row["file"]


def test_truth_references_resolve(truth: dict, entity_ids: set[str], events: list[dict]) -> None:
    event_ids = {e["id"] for e in events}
    claim_keys = set(truth["claims"])
    for claim in truth["claims"].values():
        assert claim["observed_entity"] is None or claim["observed_entity"] in entity_ids
        assert set(claim["about"]) <= entity_ids
        anchor = claim.get("valid_from_anchor_event")
        assert anchor is None or anchor in event_ids
    for edge in truth["edges"]:
        assert edge["src"] in claim_keys
        assert edge["dst"] in claim_keys | entity_ids
    for row in truth["sources"]:
        for item in row.get("evidence", []):
            scope = item.get("scope_entity")
            assert scope is None or scope in entity_ids
            assert item.get("claim", "A") in claim_keys
    for outcome in truth["telemetry_outcomes"]:
        assert outcome["after_event"] in event_ids


def test_anchor_event_matches_the_claim(truth: dict, events: list[dict]) -> None:
    claim = truth["claims"]["A"]
    anchor = next(e for e in events if e["id"] == claim["valid_from_anchor_event"])
    assert anchor["event_time"] == claim["valid_from"]
    assert anchor["entity"] == claim["observed_entity"]
    assert anchor["type"] == "module_replaced"


def test_clock_checkpoints_match_received_at(manifest: dict, truth: dict) -> None:
    """A required claim is known at a checkpoint exactly when its source has been received."""
    received = {row["file"]: None for row in truth["sources"]}
    for source in manifest["sources"]:
        received[source["file"]] = source["received_at"]
    first_seen: dict[str, str] = {}
    for row in truth["sources"]:
        if row["has_claim"]:
            seen = received[row["file"]]
            first_seen[row["claim"]] = min(first_seen.get(row["claim"], seen), seen)
    for checkpoint in truth["clock"]["checkpoints"]:
        known = {key for key, at in first_seen.items() if at <= checkpoint["as_of"]}
        assert known == set(checkpoint["known_claims"]), checkpoint["as_of"]


def test_events_have_dates_and_known_entities(events: list[dict], entity_ids: set[str]) -> None:
    assert len({e["id"] for e in events}) == len(events)
    for event in events:
        datetime.fromisoformat(event["event_time"])
        assert event["entity"] in entity_ids


def test_telemetry_is_ordered_and_on_a_real_port() -> None:
    entities = {e["id"]: e for e in load(DATA / "seed" / "entities.json")["entities"]}
    files = sorted((DATA / "events").glob("telemetry_*.json"))
    assert len(files) == 4
    for path in files:
        series = load(path)
        assert series["port"] in entities[series["node"]]["attrs"]["ports"]
        times = [s["t"] for s in series["samples"]]
        assert times == sorted(times)

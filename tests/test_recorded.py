"""The recorded model answers replay with no endpoint and no key, and hold their results."""

from collections import Counter
from pathlib import Path

import pytest

from app import db, llm, scoring
from app.ingest import run

# The model left the second expert's general advice waiting, and the truth set binds it to TRN-051.
# The owner decides which is right, so this stays visible here until then.
OPEN_DISAGREEMENT = {
    "teams_conflict.json: entity: got None, reason no_id",
    "teams_conflict.json: entity: waiting",
    "teams_conflict.json: evidence: missing"
    " {'type': 'told', 'scope_entity': 'TRN-051', 'basis': 'message'}",
    "teams_conflict.json: evidence: unexpected told on clm-005 (teams_conflict.json#seq=1,3,5)",
    "edge missing: B ABOUT TRN-051",
}


@pytest.fixture(autouse=True)
def no_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> dict:
        raise AssertionError("A recorded answer is out of date: the model was asked.")

    monkeypatch.setattr(llm, "complete_json", refuse)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)


def test_the_truth_set_holds_apart_from_the_open_disagreement(tmp_path: Path) -> None:
    assert set(scoring.score(tmp_path)["problems"]) == OPEN_DISAGREEMENT


def test_the_held_out_set_has_no_confident_wrong_binding(tmp_path: Path) -> None:
    decoys = scoring.score_decoys(tmp_path)
    counts = Counter(decoy["result"] for decoy in decoys)
    assert counts["error"] == 0
    assert counts["confident_wrong"] == 0
    assert counts["no_claim"] == 0
    assert counts["waited_right"] + counts["bound_right"] == 16


def test_the_clock_decides_what_is_known(tmp_path: Path) -> None:
    before = run(tmp_path / "before.db", until="2026-10-14T22:00:00")
    with db.session(before) as conn:
        assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM event").fetchone()[0] == 6
        assert conn.execute("SELECT mode FROM ingest_log").fetchone()["mode"] == "recorded"
    after = run(tmp_path / "after.db", until="2026-10-15T00:00:00")
    with db.session(after) as conn:
        assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 2


def test_the_teller_key_never_leaves_the_store(tmp_path: Path) -> None:
    from app import export

    path = run(tmp_path / "all.db")
    with db.session(path) as conn:
        keys = [r["teller_key"] for r in conn.execute("SELECT teller_key FROM source")]
        text = str(export.graph(conn))
    assert keys
    assert not any(key in text for key in keys)

"""The recorded model answers replay with no endpoint and no key, and hold their results."""

from collections import Counter
from pathlib import Path

import pytest

from app import db, extract, llm, scoring
from app.ingest import run

@pytest.fixture(autouse=True)
def no_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> dict:
        raise AssertionError("A recorded answer is out of date: the model was asked.")

    monkeypatch.setattr(llm, "complete_json", refuse)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)


def test_the_truth_set_holds(tmp_path: Path) -> None:
    assert scoring.score(tmp_path)["problems"] == []


def test_the_held_out_result_is_the_one_recorded_in_the_changelog(tmp_path: Path) -> None:
    """A measurement, not a target. Other runs gave other numbers: see the changelog."""
    decoys = scoring.score_decoys(tmp_path)
    assert Counter(decoy["result"] for decoy in decoys) == {
        "waited_right": 11,
        "bound_right": 4,
        "confident_wrong": 1,
    }


def test_the_clock_decides_what_is_known(tmp_path: Path) -> None:
    before = run(tmp_path / "before.db", until="2026-10-14T22:00:00")
    with db.session(before) as conn:
        assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM event").fetchone()[0] == 6
        assert conn.execute("SELECT mode FROM ingest_log").fetchone()["mode"] == "recorded"
    after = run(tmp_path / "after.db", until="2026-10-15T00:00:00")
    with db.session(after) as conn:
        assert conn.execute("SELECT count(*) FROM claim").fetchone()[0] == 2


DASHES = chr(0x2013) + chr(0x2014)


def test_the_recorded_answers_hold_no_en_or_em_dashes() -> None:
    """Prints file names only, because some of these files are the held-out set's answers."""
    files = sorted(extract.EXTRACTIONS_DIR.rglob("*.json"))
    assert len(files) == 30
    dashed = [p.name for p in files if any(c in p.read_text(encoding="utf-8") for c in DASHES)]
    assert dashed == []


def test_the_teller_key_never_leaves_the_store(tmp_path: Path) -> None:
    from app import export

    path = run(tmp_path / "all.db")
    with db.session(path) as conn:
        keys = [r["teller_key"] for r in conn.execute("SELECT teller_key FROM source")]
        text = str(export.graph(conn))
    assert keys
    assert not any(key in text for key in keys)

"""Checks the held-out binding set by shape only. Its content is not used for writing rules."""

import json
from datetime import datetime
from pathlib import Path

TRUTH = Path(__file__).resolve().parent.parent / "data" / "truth"
SEED = TRUTH.parent / "seed" / "entities.json"


def test_decoys_have_expected_rows_and_known_entities() -> None:
    entity_ids = {e["id"] for e in json.loads(SEED.read_text(encoding="utf-8"))["entities"]}
    expected = json.loads((TRUTH / "expected_decoys.json").read_text(encoding="utf-8"))["decoys"]
    files = {p.name for p in (TRUTH / "decoys").iterdir()}
    assert files == {row["file"] for row in expected}
    assert len(expected) == 16
    for row in expected:
        datetime.fromisoformat(row["received_at"])
        if row["expected_binding_status"] == "bound":
            assert row["expected_entity"] in entity_ids
        else:
            assert row["expected_entity"] is None and row["expected_reason"]

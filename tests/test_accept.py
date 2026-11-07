"""The acceptance table holds: every computed row passes, on the recorded data with no key."""

from app import accept


def test_every_computed_acceptance_row_holds() -> None:
    rows = accept.run_cases()
    codes = {row[0] for row in rows}
    assert {"A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11"} <= codes
    failed = [row for row in rows if row[4] in ("FAIL", "ERROR")]
    assert failed == []
    assert "Case | Asked | Expected | Observed | Result" in accept.table(rows)

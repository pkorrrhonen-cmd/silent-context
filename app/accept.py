"""The acceptance cases of the build plan, run on the recorded data and written as one table.

`uv run python -m app.accept` prints the table and writes `docs/acceptance.md`. It needs no model and
no key: the stores are built from the recorded answers at each case's clock, as the tests do. The
checks are the same as in `tests/test_claims.py`; the table exists so the result can be shown on a
slide without reading the tests.
"""

import json
import re
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

from app import db, ingest, scoring, view
from app.claims import PROHIBITION, access_for, claims_for
from app.sources import ROOT, load_manifest

OUTPUT = ROOT / "docs" / "acceptance.md"
REPEATS = ROOT / "data" / "truth" / "held_out_repeats.json"

SYMPTOM = "link up, counters zero after SFP replacement"
BEFORE_CAPTURE = "2026-10-14T22:00:00"
AFTER_CAPTURE = "2026-10-20T12:00:00"
KEY_MOVED = "2026-10-21T00:00:00"
DURING_FAULT = "2026-10-21T10:50:00"
AFTER_FIRMWARE = "2026-10-29T00:00:00"
AFTER_FAILURE = "2026-10-31T00:00:00"
AFTER_DISPUTE = "2026-11-03T00:00:00"
COUNT_WORDS = re.compile(r"\b(two|twice|several|independent|percent)\b|%", re.I)


class Stores:
    """The store as it stood at each clock value, built once per clock in a folder of its own."""

    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.paths: dict[str, Path] = {}
        self.open: list = []

    def at(self, clock: str):
        """One connection at a time: an earlier one with an unwritten log would lock the file."""
        self.release()
        if clock not in self.paths:
            self.paths[clock] = ingest.run(self.workdir / f"{len(self.paths)}.db", until=clock)
        session = db.session(self.paths[clock])
        conn = session.__enter__()
        self.open.append(session)
        return conn

    def release(self) -> None:
        """Closes the connections a case opened, so the next case meets no lock on the same file."""
        for session in self.open:
            session.__exit__(None, None, None)
        self.open = []


def erkki(answer: dict) -> dict:
    return next(c for c in answer["claims"] if c["observed_entity"] == "TRN-042")


def short(iso: str) -> str:
    day = iso[:10].split("-")
    return f"{int(day[2])}.{int(day[1])}."


def held(answer: dict) -> str:
    return "held back" if answer["prohibition"] == PROHIBITION else "no prohibition"


# Each case: code, what is asked, what the plan expects, and a function that returns
# (what was observed, whether it holds). The wording of "expected" follows the build plan.


def case_a0(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, conn=s.at(BEFORE_CAPTURE))
    return (
        f"{a['tier']}, reason {a['reason_code']}, ask {a['ask_group']}",
        a["tier"] == "unknown" and a["reason_code"] == "no_claims" and a["ask_group"] == "transmission-oncall",
    )


def case_a1_no_counters(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, conn=s.at(AFTER_CAPTURE))
    return (
        f"{a['tier']}, {a['match_level']}, {a['action_kind']}, {held(a)}, called an inference",
        a["tier"] == "check_first"
        and a["match_level"] == "same_class"
        and a["action_kind"] == "read"
        and a["prohibition"] == PROHIBITION
        and "inference" in a["match_note"],
    )


def case_a1_zero(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=s.at(AFTER_CAPTURE))
    claim = erkki(a)
    channels = sorted({src["channel"] for src in claim["sources"]})
    return (
        f"{a['tier']}, {a['match_level']}, {a['action_kind']}, {held(a)}; scope {claim['scope_status']},"
        f" sources {' and '.join(channels)}",
        a["tier"] == "propose"
        and a["match_level"] == "same_class"
        and a["action_kind"] == "bounce_interface"
        and a["prohibition"] == PROHIBITION
        and claim["scope_status"] == "undefined"
        and channels == ["email", "teams"],
    )


def case_a1_telemetry(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, conn=s.at(DURING_FAULT))
    used = a["observed_used"]
    return (
        f"counters {used['counters']} from {used['counters_from']}; {a['tier']}",
        used == {"counters": "zero", "counters_from": "telemetry"} and a["tier"] == "propose",
    )


def case_a2_guess(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-100", SYMPTOM, observed={"counters": "zero"}, conn=s.at(AFTER_CAPTURE))
    return (
        f"{a['match_level']}, {a['tier']}, {a['action_kind']}; \"{a['match_note'][:8]}...\"",
        a["match_level"] == "similar_guess"
        and a["tier"] == "check_first"
        and a["action_kind"] == "read"
        and a["match_note"].startswith("A guess"),
    )


def case_a2_after_failure(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-100", SYMPTOM, observed={"counters": "zero"}, conn=s.at(AFTER_FAILURE))
    claim = erkki(a)
    failure = any(e["type"] == "reported_failure" and e["scope"] == "TRN-100" for e in claim["evidence"])
    return (
        f"{a['tier']}, {a['action_kind']}; the advice {claim['status_for_entity']}, match {claim['match_level']},"
        f" narrowed to 4.x firmware, failure on TRN-100 shown",
        a["tier"] != "propose"
        and a["action_kind"] != "bounce_interface"
        and claim["status_for_entity"] == "not_applicable"
        and claim["match_level"] == "none"
        and "4.x firmware" in claim["match_note"]
        and failure,
    )


def case_a2_older_still(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=s.at(AFTER_FAILURE))
    return (
        f"{a['tier']}, {a['match_level']}, scope confirmed as 4.x firmware",
        a["tier"] == "propose"
        and a["match_level"] == "same_class"
        and "inference" not in a["match_note"]
        and "4.x firmware" in a["match_note"],
    )


def case_a3(s: Stores) -> tuple[str, bool]:
    conn = s.at(AFTER_CAPTURE)
    symptom = "intermittent CRC errors on uplink"
    a = claims_for("TRN-051", symptom, conn=conn)
    gap = conn.execute("SELECT * FROM gap_log WHERE symptom = ?", (symptom,)).fetchone()
    return (
        f"{a['tier']}, reason {a['reason_code']}, ask {a['ask_group']}, no claims, gap logged for"
        f" {gap['ask_group'] if gap else 'nobody'}",
        a["tier"] == "unknown"
        and a["reason_code"] == "no_claims"
        and a["ask_group"] == "transmission-oncall"
        and a["claims"] == []
        and gap is not None
        and gap["ask_group"] == "transmission-oncall",
    )


def case_a4_before(s: Stores) -> tuple[str, bool]:
    a = access_for("SITE-NILO", conn=s.at(AFTER_CAPTURE))
    age = a["claims"][0]["info_age_days"]
    return (
        f"{a['tier']}, the grey box, information age {age} days",
        a["tier"] == "propose" and "grey box" in a["next_step"] and age == 47,
    )


def case_a4_after(s: Stores) -> tuple[str, bool]:
    a = access_for("SITE-NILO", conn=s.at(KEY_MOVED))
    statuses = [c["status_for_entity"] for c in a["claims"]]
    return (
        f"the maintenance hut; boundary known; {' and '.join(statuses)}; the old one valid_to"
        f" {a['claims'][1]['valid_to']}",
        "maintenance hut" in a["next_step"]
        and a["boundary_known"] is True
        and statuses == ["active", "superseded"]
        and a["claims"][1]["valid_to"] == "2026-10-19",
    )


def case_a4_point(s: Stores) -> tuple[str, bool]:
    a = access_for("SITE-NILO", at="2026-10-10", conn=s.at(KEY_MOVED))
    return (
        "the grey box; boundary known; the hut not in the evidence",
        "grey box" in a["next_step"]
        and a["boundary_known"] is True
        and "maintenance hut" not in a["evidence_rendered"],
    )


def case_a4_undated(s: Stores) -> tuple[str, bool]:
    variant = load_manifest()["variants"][0]
    path = ingest.run(
        s.workdir / "variant.db", until=variant["received_at"], replacing={variant["replaces"]: variant}
    )
    with db.session(path) as conn:
        a = access_for("SITE-NILO", at="2026-10-10", conn=conn)
        active = [c for c in a["claims"] if c["status_for_entity"] == "active"]
        current = access_for("SITE-NILO", conn=conn)
    return (
        f"boundary {'not known' if a['boundary_known'] is False else 'known'}; {len(active)} may hold;"
        f" now the hut, the old end {current['claims'][1]['valid_to_basis']}",
        a["boundary_known"] is False
        and "not known" in a["next_step"]
        and len(active) == 2
        and "maintenance hut" in current["next_step"]
        and current["claims"][1]["valid_to_basis"] == "superseded_end_unknown",
    )


def case_a5(s: Stores) -> tuple[str, bool]:
    conn = s.at(AFTER_FIRMWARE)
    updated = claims_for("TRN-042", SYMPTOM, observed={"counters": "zero"}, conn=conn)
    other = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=conn)
    u, o = erkki(updated), erkki(other)
    return (
        f"TRN-042: {updated['tier']}, {u['status_for_entity']}, 4.8 to 4.9 named; TRN-051: {other['tier']},"
        f" {o['status_for_entity']}",
        updated["tier"] == "check_first"
        and updated["action_kind"] == "read"
        and u["status_for_entity"] == "recheck"
        and "4.8" in (u["status_note"] or "")
        and "4.9" in (u["status_note"] or "")
        and other["tier"] == "propose"
        and o["status_for_entity"] == "active",
    )


def case_a6(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=s.at(AFTER_CAPTURE))
    told = [line for line in erkki(a)["evidence_rendered"].splitlines() if line.startswith("Told:")]
    clean = True
    for clock in (AFTER_CAPTURE, AFTER_FAILURE, AFTER_DISPUTE):
        rendered = claims_for("TRN-042", SYMPTOM, conn=s.at(clock))["evidence_rendered"]
        clean = clean and bool(rendered) and not COUNT_WORDS.search(rendered)
    return (
        f"{len(told)} Told line, Teams and email on it; no count word at three clocks: {'none' if clean else 'FOUND'}",
        len(told) == 1
        and "teams/Network Expert" in told[0]
        and "email/Network Expert" in told[0]
        and clean,
    )


def case_a7(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}, conn=s.at(AFTER_DISPUTE))
    waiting = next((c for c in a["claims"] if c["binding_status"] == "waiting"), None)
    return (
        f"{a['tier']}, {a['action_kind']}, does not choose; the first {erkki(a)['status_for_entity']},"
        f" the second {waiting['status_for_entity'] if waiting else 'missing'} and not offered",
        a["tier"] == "check_first"
        and a["action_kind"] == "read"
        and "does not choose" in a["next_step"]
        and erkki(a)["status_for_entity"] == "disputed"
        and waiting is not None
        and waiting["status_for_entity"] == "disputed"
        and "not offered as advice" in waiting["match_note"],
    )


def case_a8_no_report(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, conn=s.at(AFTER_CAPTURE))
    return (
        f"{a['action_kind']}, {held(a)}",
        a["action_kind"] not in ("reboot", "replace_hw") and a["prohibition"] == PROHIBITION,
    )


def case_a8_bounce_done(s: Stores) -> tuple[str, bool]:
    a = claims_for("TRN-051", SYMPTOM, observed={"bounce_done": True}, conn=s.at(AFTER_CAPTURE))
    return (f"{a['action_kind']}, {held(a)}", a["action_kind"] == "read" and a["prohibition"] == PROHIBITION)


def case_a8_bounce_failed(s: Stores) -> tuple[str, bool]:
    a = claims_for(
        "TRN-051",
        SYMPTOM,
        observed={"counters": "zero", "bounce_done": True, "bounce_failed": True},
        conn=s.at(AFTER_CAPTURE),
    )
    return (
        f"{a['tier']}, {a['action_kind']}, {held(a)}",
        a["tier"] == "propose" and a["action_kind"] == "reboot" and a["prohibition"] is None,
    )


def case_a9(s: Stores) -> tuple[str, bool]:
    decoys = scoring.score_decoys(s.workdir / "decoys")
    counts = Counter(d["result"] for d in decoys)
    repeats = json.loads(REPEATS.read_text(encoding="utf-8")) if REPEATS.exists() else None
    runs = " ".join(str(n) for n in repeats["confident_wrong_per_run"]) if repeats else "not measured"
    return (
        f"of {len(decoys)}: waited right {counts['waited_right']}, bound right {counts['bound_right']},"
        f" over-cautious {counts['over_cautious']}, confidently wrong {counts['confident_wrong']},"
        f" errors {counts['error']}; five repeats, wrong per run: {runs}",
        counts["error"] == 0 and len(decoys) == 16,
    )


def case_a11(s: Stores) -> tuple[str, bool]:
    state = view.state(s.at("2026-10-15T00:00:00"))
    m = state["metrics"]
    elisa = [src for src in state["sources"] if src["origin"] == "elisa"]
    unchanged = all(src["unchanged"] is True for src in elisa)
    return (
        f"conversations started {m['conversations_started']}, actions asked {m['actions_asked_of_specialists']},"
        f" Elisa's {len(elisa)} files shown unchanged by checksum: {'yes' if unchanged else 'NO'}",
        m["conversations_started"] == 0
        and m["actions_asked_of_specialists"] == 0
        and len(elisa) == 2
        and unchanged,
    )


AFTER_RECORD = "2026-10-25T09:40:00"
AFTER_AGENT_ACTED = "2026-10-25T09:50:00"


def case_a12(s: Stores) -> tuple[str, bool]:
    """The policy on who acts: a person the first time, the agent once its own log shows a carried-out success."""
    first = claims_for("TRN-051", SYMPTOM, conn=s.at(DURING_FAULT))
    s.release()
    path = s.paths[DURING_FAULT]
    ingest.run(path, until=AFTER_RECORD)
    with db.session(path) as conn:
        third = claims_for("TRN-063", SYMPTOM, conn=conn)
    ingest.run(path, until=AFTER_AGENT_ACTED)
    with db.session(path) as conn:
        row = conn.execute("SELECT done_by, outcome FROM answer_log WHERE id = ?", (third["answer_id"],)).fetchone()
    s.paths.pop(DURING_FAULT)  # that store now holds this case's log; the others build their own
    return (
        f"TRN-051 21.10.: {first['tier']}, {first['who_acts']}; TRN-063 25.10.: {third['tier']}, {third['who_acts']};"
        f" done by {row['done_by']}, {row['outcome']}",
        first["who_acts"] == "person" and third["who_acts"] == "agent" and third["tier"] == "propose"
        and row["done_by"] == "agent" and row["outcome"] == "Counters rising afterwards",
    )


CASES = [
    ("A0", "TRN-051, the symptom, before anything is captured (14.10. 22:00)",
     "I don't know, reason no claims, ask transmission-oncall", case_a0),
    ("A1", "TRN-051, the symptom, counters not reported (20.10.)",
     "check first, same class, read the counters, reboot and replacement held back, reach called an inference",
     case_a1_no_counters),
    ("A1", "TRN-051, counters reported zero (20.10.)",
     "propose the bounce, same class, held back; the claim's scope undefined, Teams and email as one telling",
     case_a1_zero),
    ("A1", "TRN-051 during the fault, nothing reported (21.10. 10:50)",
     "the agent reads zero counters from telemetry itself and proposes", case_a1_telemetry),
    ("A2", "TRN-100, a newer unit, before anyone narrows the advice (20.10.)",
     "named a guess, check first, read; never a proposal", case_a2_guess),
    ("A2", "TRN-100 after the failure and the narrowing (31.10.)",
     "not proposed, not the bounce; the advice shown as not applicable with the reported failure",
     case_a2_after_failure),
    ("A2", "TRN-051 after the narrowing (31.10.)",
     "still proposed, same class, now a confirmed scope", case_a2_older_still),
    ("A3", "TRN-051, a different symptom (20.10.)",
     "I don't know, no claims, ask transmission-oncall, the gap logged", case_a3),
    ("A4", "Access to Nilo before the key moved (20.10.)",
     "the grey box, with the information age in days", case_a4_before),
    ("A4", "Access to Nilo after the move (21.10.)",
     "the maintenance hut; the old location superseded with its end date", case_a4_after),
    ("A4", "Access to Nilo at a point in world time, 10.10.",
     "the grey box, the hut not shown", case_a4_point),
    ("A4", "The same move with no date in the email",
     "both may hold, the boundary not known, the old end marked unknown", case_a4_undated),
    ("A5", "After a firmware update on TRN-042 only (29.10.)",
     "TRN-042: check first, recheck, the versions named; TRN-051: proposed, active", case_a5),
    ("A6", "Teams and email from the same teller",
     "one Told line; no two, twice, several, independent or percent in any rendered evidence", case_a6),
    ("A7", "Two experts disagree (3.11.)",
     "check first, read the counters, the agent does not choose; both shown, the waiting one not offered",
     case_a7),
    ("A8", "The prohibition with nothing reported", "no reboot or replacement, held back", case_a8_no_report),
    ("A8", "The prohibition after a bounce with no result", "read, still held back", case_a8_bounce_done),
    ("A8", "The prohibition after a failed bounce", "a reboot may be proposed, nothing held back",
     case_a8_bounce_failed),
    ("A9", "The held-out binding set, 16 synthetic sources",
     "unclear cases wait with a reason, controls bind; the wrong ones counted, not tuned", case_a9),
    ("A11", "The extra-work panel (15.10.)",
     "conversations started 0, actions asked 0, Elisa's files shown unchanged by checksum", case_a11),
    ("A12", "Who acts: TRN-051 on 21.10., then TRN-063 on 25.10. after the first was carried out",
     "a person the first time; the agent once its own log shows the step carried out on this class with the counters rising,"
     " and the agent's own bounce recorded as its own from the devices", case_a12),
]

BY_HAND = [
    ("A10", "A clean install from the README into an empty folder, with no key",
     "the seeded store, the agent and the graph work; ingest reads the recorded answers and says it needs a model only for a changed prompt",
     "Passed on 7.11.2026 from `git archive` into an empty folder: 150 tests, seed, ingest, truth report, the agent, both exports (CHANGELOG, session 3)",
     "by hand"),
]


def run_cases() -> list[tuple[str, str, str, str, str]]:
    """Every row of the table: code, asked, expected, observed, result."""
    rows = []
    with tempfile.TemporaryDirectory() as temp:
        stores = Stores(Path(temp))
        try:
            for code, asked, expected, check in CASES:
                try:
                    observed, ok = check(stores)
                    result = "measured" if code == "A9" else ("ok" if ok else "FAIL")
                    if code == "A9" and not ok:
                        result = "FAIL"
                except Exception as error:  # the table must say so, not stop
                    observed, result = f"{type(error).__name__}: {error}", "ERROR"
                finally:
                    stores.release()
                rows.append((code, asked, expected, observed, result))
        finally:
            stores.release()
    for code, asked, expected, observed, result in BY_HAND:
        rows.append((code, asked, expected, observed, result))
    return sorted(rows, key=lambda row: (int(row[0][1:]), CASES_ORDER.get(row[1], 0)))


CASES_ORDER = {asked: index for index, (_, asked, _, _) in enumerate(CASES)}


def table(rows: list[tuple[str, str, str, str, str]]) -> str:
    lines = ["| Case | Asked | Expected | Observed | Result |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def document(rows: list[tuple[str, str, str, str, str]]) -> str:
    computed = [row for row in rows if row[4] in ("ok", "FAIL", "ERROR", "measured")]
    passed = sum(1 for row in computed if row[4] in ("ok", "measured"))
    return (
        "# Acceptance cases\n\n"
        f"Written by `uv run python -m app.accept` on {date.today().isoformat()} from the recorded answers, with no"
        " model and no key. The cases are the build plan's A1 to A11, with A0 for the question before anything"
        " is captured. The stores are built at each case's clock from `data/`, as the tests do; the checks are"
        " the ones in `tests/test_claims.py`. A9 reports numbers and is not a pass or a fail: they describe this"
        " set of 16 synthetic sources only. A10 was done by hand and is quoted from the changelog.\n\n"
        f"Computed rows holding: {passed} of {len(computed)}.\n\n" + table(rows) + "\n"
    )


def main() -> None:
    rows = run_cases()
    text = document(rows)
    OUTPUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"Written to {OUTPUT}")


if __name__ == "__main__":
    main()

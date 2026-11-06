"""Scores a run against the truth set, and binding against the held-out set.

The report prints numbers for the held-out set and nothing of its content, because whoever writes the
binding rules reads this output.
"""

import hashlib
import json
import re
import sqlite3
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from app import db, extract, ingest
from app.resolve import Graph
from app.sources import ROOT, load_manifest

TRUTH_DIR = ROOT / "data" / "truth"
DECOY_DIR = TRUTH_DIR / "decoys"
DECOY_RECORD_DIR = extract.EXTRACTIONS_DIR / "decoys"


@dataclass
class SourceScore:
    file: str
    claim: str
    cells: dict[str, bool] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    def check(self, column: str, ok: bool, detail: str = "") -> None:
        self.cells[column] = self.cells.get(column, True) and ok
        if not ok:
            self.problems.append(f"{self.file}: {column}: {detail}")


def _claim(conn: sqlite3.Connection, claim_id: str) -> sqlite3.Row:
    return conn.execute("SELECT * FROM claim WHERE id = ?", (claim_id,)).fetchone()


def _message_seqs(source_ref: str | None) -> list[int]:
    match = re.search(r"#seq=([\d,]+)", source_ref or "")
    return [int(seq) for seq in match.group(1).split(",")] if match else []


def _evidence_matches(row: sqlite3.Row, want: dict, ids: dict[str, str], default: str) -> bool:
    key = want.get("claim", default)
    return (
        row["type"] == want["type"]
        and row["claim_id"] == ids.get(key)
        and row["basis"] == want["basis"]
        and ("scope_entity" not in want or row["scope_entity"] == want["scope_entity"])
        and want.get("excerpt_contains", "").casefold() in (row["excerpt"] or "").casefold()
        and ("message_seq" not in want or want["message_seq"] in _message_seqs(row["source_ref"]))
        and ("day" not in want or (row["event_time"] or "").startswith(want["day"]))
    )


def _score_source(conn: sqlite3.Connection, row: dict, truth: dict, ids: dict[str, str]) -> SourceScore:
    file = row["file"]
    score = SourceScore(file, row.get("claim", ""))
    log = conn.execute("SELECT claim_ids FROM ingest_log WHERE file = ?", (file,)).fetchone()
    touched: list[str] = json.loads(log["claim_ids"]) if log else []

    score.check("found", bool(touched) == row["has_claim"], f"claims={touched}")
    if not row["has_claim"]:
        return score

    expected = truth["claims"][row["claim"]]
    if row["new_claim"]:
        fresh = [claim_id for claim_id in touched if claim_id not in ids.values()]
        match = next(
            (c for c in fresh if _claim(conn, c)["observed_entity"] == expected["observed_entity"]),
            fresh[0] if fresh else None,
        )
        if match is None:
            score.check("merged", False, "no new claim")
            return score
        ids[row["claim"]] = match
        extras = len(fresh) - 1 - len(row.get("optional_claims", []))
        score.check("merged", extras <= 0, f"{extras} unexpected extra claims: {fresh}")
    else:
        extras = [c for c in touched if c != ids.get(row["claim"])]
        score.check(
            "merged",
            ids.get(row["claim"]) in touched and len(extras) <= len(row.get("optional_claims", [])),
            f"expected {row['claim']}={ids.get(row['claim'])}, touched {touched}",
        )
    claim_id = ids.get(row["claim"])
    if claim_id is None:
        return score
    claim = _claim(conn, claim_id)

    if row["new_claim"]:
        score.check(
            "entity",
            claim["observed_entity"] == expected["observed_entity"],
            f"got {claim['observed_entity']}, reason {claim['binding_reason']}",
        )
        score.check("entity", claim["binding_status"] == row["binding_status"], claim["binding_status"])
        score.check("entity", claim["binding_reason"] == row["binding_reason"], claim["binding_reason"])
        score.check(
            "time",
            (claim["valid_from"], claim["valid_from_basis"])
            == (expected["valid_from"], expected["valid_from_basis"]),
            f"got valid_from {claim['valid_from']} ({claim['valid_from_basis']})",
        )
        score.check(
            "time",
            claim["valid_to"] == expected.get("valid_to"),
            f"got valid_to {claim['valid_to']}",
        )
        scope = (claim["scope_text"] or "").casefold()
        if "scope_text_any_of" in expected:
            score.check(
                "scope",
                any(p.casefold() in scope for p in expected["scope_text_any_of"]),
                f"got {claim['scope_text']!r}",
            )
        else:
            score.check("scope", claim["scope_text"] is None, f"got {claim['scope_text']!r}")
        for banned in expected.get("scope_text_must_not_contain", []):
            score.check("scope", banned.casefold() not in scope, f"contains {banned}")

    source = conn.execute(
        "SELECT source_time_text FROM source WHERE claim_id = ? AND ref LIKE ?",
        (claim_id, f"{file}%"),
    ).fetchone()
    score.check(
        "time",
        source is not None and source["source_time_text"] == row["source_time_text"],
        f"source time {source['source_time_text'] if source else None!r}",
    )

    found = conn.execute(
        "SELECT * FROM evidence_event WHERE source_ref LIKE ?", (f"{file}%",)
    ).fetchall()
    unmatched = list(found)
    for want in row["evidence"]:
        hit = next((e for e in unmatched if _evidence_matches(e, want, ids, row["claim"])), None)
        score.check("evidence", hit is not None, f"missing {want}")
        if hit is not None:
            unmatched.remove(hit)
    expected_ids = set(ids.values())
    for extra in unmatched:
        score.check(
            "evidence",
            extra["claim_id"] not in expected_ids,
            f"unexpected {extra['type']} on {extra['claim_id']} ({extra['source_ref']})",
        )
    return score


def _score_claims(conn: sqlite3.Connection, truth: dict, ids: dict[str, str]) -> list[str]:
    problems = []
    for key, expected in truth["claims"].items():
        if key not in ids:
            if not expected.get("optional"):
                problems.append(f"claim {key}: never created")
            continue
        claim = _claim(conn, ids[key])
        text = claim["claim_text"].casefold()
        for phrase in expected.get("claim_text_must_mention", []):
            if phrase.casefold() not in text:
                problems.append(f"claim {key}: text does not mention {phrase!r}: {claim['claim_text']}")
        hedges = expected.get("claim_text_must_keep_one_hedge")
        if hedges and not any(h.casefold() in text for h in hedges):
            problems.append(f"claim {key}: no hedge kept: {claim['claim_text']}")
        if claim["kind"] != expected["kind"]:
            problems.append(f"claim {key}: kind {claim['kind']}")
        for field_name in ("check_kind", "action_kind"):
            if field_name in expected and claim[field_name] != expected[field_name]:
                problems.append(f"claim {key}: {field_name} is {claim[field_name]}")
        for field_name in ("check_step", "action", "do_not_before"):
            for phrase in expected.get(f"{field_name}_must_mention", []):
                if phrase.casefold() not in (claim[field_name] or "").casefold():
                    problems.append(f"claim {key}: {field_name} {claim[field_name]!r} lacks {phrase!r}")
        final = expected.get("scope_refined_by", expected)
        if "scope_status" in final and claim["scope_status"] != final["scope_status"]:
            problems.append(f"claim {key}: scope status {claim['scope_status']}")
        if "applies_to" in final and claim["applies_to"] != final["applies_to"]:
            problems.append(f"claim {key}: applies to {claim['applies_to']}")
        must = final.get("scope_text_must_contain")
        if must and must.casefold() not in (claim["scope_text"] or "").casefold():
            problems.append(f"claim {key}: scope {claim['scope_text']!r} lacks {must!r}")
        if "superseded_at" in expected and claim["superseded_at"] != expected["superseded_at"]:
            problems.append(f"claim {key}: superseded_at {claim['superseded_at']}")
        for estimate in expected.get("estimates", []):
            row = conn.execute(
                "SELECT value_text, role FROM estimate WHERE entity = ? AND attribute = ?",
                (estimate["entity"], estimate["attribute"]),
            ).fetchone()
            if (
                row is None
                or estimate["value_text"] not in row["value_text"]
                or row["role"] != estimate["role"]
            ):
                problems.append(f"claim {key}: estimate {estimate} got {dict(row) if row else None}")
    for outcome in truth["telemetry_outcomes"]:
        seen = conn.execute(
            "SELECT 1 FROM evidence_event WHERE basis = 'telemetry' AND scope_entity = ?",
            (outcome["entity"],),
        ).fetchone()
        if bool(seen) != (outcome["expected"] == "reported_success"):
            problems.append(f"telemetry outcome on {outcome['entity']}: seen={bool(seen)}")
    for edge in truth["edges"]:
        src, dst = ids.get(edge["src"]), ids.get(edge["dst"], edge["dst"])
        found = conn.execute(
            "SELECT 1 FROM edge WHERE src = ? AND rel = ? AND dst = ?", (src, edge["rel"], dst)
        ).fetchone()
        if not found:
            problems.append(f"edge missing: {edge['src']} {edge['rel']} {edge['dst']}")
    return problems


def _score_clock(truth: dict, ids: dict[str, str], workdir: Path) -> list[str]:
    problems = []
    for index, checkpoint in enumerate(truth["clock"]["checkpoints"]):
        path = ingest.run(workdir / f"clock{index}.db", until=checkpoint["as_of"])
        with db.session(path) as conn:
            present = {row["id"] for row in conn.execute("SELECT id FROM claim")}
            optional = set(checkpoint.get("optional_known_claims", []))
            known = {key for key, claim_id in ids.items() if claim_id in present} - optional
            if known != set(checkpoint["known_claims"]):
                problems.append(f"clock {checkpoint['as_of']}: known {sorted(known)}")
            if "A" in ids and ids["A"] in present:
                status = _claim(conn, ids["A"])["scope_status"]
                wanted = "confirmed" if checkpoint["as_of"] >= "2026-10-30T23:00:00" else "undefined"
                if status != wanted:
                    problems.append(f"clock {checkpoint['as_of']}: scope of A is {status}")
    return problems


def _score_variant(truth: dict, ids: dict[str, str], refresh: bool, workdir: Path) -> list[str]:
    variant = load_manifest()["variants"][0]
    row = truth["variants"][0]
    path = ingest.run(
        workdir / "variant.db",
        until=variant["received_at"],
        replacing={variant["replaces"]: variant},
        refresh=refresh,
    )
    problems = []
    with db.session(path) as conn:
        log = conn.execute(
            "SELECT claim_ids FROM ingest_log WHERE file = ?", (variant["file"],)
        ).fetchone()
        new = json.loads(log["claim_ids"]) if log else []
        if len(new) != 1:
            return [f"variant: touched {new}"]
        old = _claim(conn, ids["K1"]) if "K1" in ids else None
        replacement = _claim(conn, new[0])
        if old is None:
            return ["variant: K1 missing"]
        for field_name, value in row["expect_on_k1"].items():
            if old[field_name] != value:
                problems.append(f"variant: K1 {field_name} is {old[field_name]}, wanted {value}")
        for field_name, value in row["expect_on_k2"].items():
            if replacement[field_name] != value:
                problems.append(
                    f"variant: K2 {field_name} is {replacement[field_name]}, wanted {value}"
                )
        edge = conn.execute(
            "SELECT 1 FROM edge WHERE src = ? AND rel = 'SUPERSEDES' AND dst = ?",
            (replacement["id"], old["id"]),
        ).fetchone()
        if not edge:
            problems.append("variant: no SUPERSEDES edge")
    return problems


def _score_decoy(row: dict, workdir: Path, refresh: bool, record_dir: Path) -> dict:
    """One held-out source in a store of its own, so no other source can help or hurt it."""
    path = db.build(workdir / f"{row['file']}.db")
    with db.session(path) as conn:
        graph = Graph.load(conn)
        entry = {"file": row["file"], "received_at": row["received_at"]}
        try:
            ingest.ingest_file(
                conn, graph, entry, directory=DECOY_DIR, cache_dir=record_dir, refresh=refresh
            )
        except ingest.llm.ModelNotConfigured:
            raise
        except Exception as error:
            return {
                "file": row["file"],
                "category": row["category"],
                "result": "error",
                "error": type(error).__name__,
            }
        claims = conn.execute(
            "SELECT observed_entity, binding_status, binding_reason FROM claim"
        ).fetchall()
    result = {"file": row["file"], "category": row["category"]}
    bound = [claim for claim in claims if claim["binding_status"] == "bound"]
    if not claims:
        result["result"] = "no_claim"
    elif any(claim["observed_entity"] != row["expected_entity"] for claim in bound):
        result["result"] = "confident_wrong"
    elif row["expected_binding_status"] == "bound":
        result["result"] = "bound_right" if bound else "over_cautious"
    else:
        result["result"] = "waited_right"
        result["reason_right"] = all(
            claim["binding_reason"] == row["expected_reason"] for claim in claims
        )
    return result


def score_decoys(
    workdir: Path, refresh: bool = False, record_dir: Path = DECOY_RECORD_DIR
) -> list[dict]:
    rows = json.loads((TRUTH_DIR / "expected_decoys.json").read_text(encoding="utf-8"))["decoys"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(lambda row: _score_decoy(row, workdir, refresh, record_dir), rows))


def repeat_decoys(runs: int) -> None:
    """Fresh model calls with the prompt unchanged, to see how much the result moves between runs.

    The recorded answers are not touched. Prints and stores numbers and file names only.
    """
    results = []
    for number in range(1, runs + 1):
        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            decoys = score_decoys(workdir, record_dir=workdir / "answers")
        counts = Counter(decoy["result"] for decoy in decoys)
        results.append(
            {
                "run": number,
                "counts": dict(counts),
                "reason_right": sum(1 for decoy in decoys if decoy.get("reason_right")),
                "wrong_files": sorted(
                    decoy["file"] for decoy in decoys if decoy["result"] == "confident_wrong"
                ),
                "wrong_categories": dict(
                    Counter(d["category"] for d in decoys if d["result"] == "confident_wrong")
                ),
            }
        )
        print(f"Run {number}: {results[-1]['counts']}, reason right {results[-1]['reason_right']}", flush=True)
    wrong = [r["counts"].get("confident_wrong", 0) for r in results]
    record = {
        "note": "Repeats of the held-out set with the prompt unchanged and no rule tuned to it. These"
        " are numbers and file names only. They describe this set of 16 synthetic sources.",
        "model": ingest.llm.model_name(),
        "prompt_sha256": hashlib.sha256(extract.SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "runs": results,
        "confident_wrong_per_run": wrong,
        "distinct_wrong_files": sorted({f for r in results for f in r["wrong_files"]}),
        "tokens": dict(ingest.llm.usage),
    }
    (TRUTH_DIR / "held_out_repeats.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Confidently wrong per run, of 16: {wrong}")
    print(f"Distinct files ever wrong: {len(record['distinct_wrong_files'])}")
    print(f"Tokens: {record['tokens']}")


def score(workdir: Path, refresh: bool = False) -> dict:
    truth = json.loads((TRUTH_DIR / "expected_claims.json").read_text(encoding="utf-8"))
    path = ingest.run(workdir / "all.db", refresh=refresh)
    ids: dict[str, str] = {}
    with db.session(path) as conn:
        rows = [_score_source(conn, row, truth, ids) for row in truth["sources"]]
        claim_problems = _score_claims(conn, truth, ids)
        claims = conn.execute("SELECT * FROM claim ORDER BY id").fetchall()
        listing = []
        for claim in claims:
            evidence = conn.execute(
                "SELECT type, scope_entity FROM evidence_event WHERE claim_id = ? ORDER BY id",
                (claim["id"],),
            ).fetchall()
            sources = conn.execute(
                "SELECT ref FROM source WHERE claim_id = ? ORDER BY id", (claim["id"],)
            ).fetchall()
            listing.append(
                {
                    **dict(claim),
                    "evidence": [f"{e['type']} {e['scope_entity'] or ''}".strip() for e in evidence],
                    "sources": [s["ref"] for s in sources],
                }
            )
    clock = _score_clock(truth, ids, workdir)
    variant = _score_variant(truth, ids, refresh, workdir)
    return {
        "rows": rows,
        "problems": [p for row in rows for p in row.problems] + claim_problems + clock + variant,
        "claims": listing,
    }


def report(refresh: bool = False) -> None:
    with tempfile.TemporaryDirectory() as temp:
        workdir = Path(temp)
        result = score(workdir, refresh)
        decoys = score_decoys(workdir, refresh)

    print("## Claims\n")
    for claim in result["claims"]:
        print(f"**{claim['id']}** ({claim['kind']}, {claim['binding_status']}"
              f"{', ' + claim['binding_reason'] if claim['binding_reason'] else ''})")
        print(f"- text: {claim['claim_text']}")
        print(f"- observed on: {claim['observed_entity']}")
        print(f"- scope: {claim['scope_text']!r} ({claim['scope_status']}, {claim['applies_to']})")
        print(f"- valid: {claim['valid_from']} ({claim['valid_from_basis']}) to {claim['valid_to']}"
              f" ({claim['valid_to_basis']}); received {claim['received_at']};"
              f" superseded {claim['superseded_at']}")
        print(f"- sources: {claim['sources']}")
        print(f"- evidence: {claim['evidence']}\n")

    columns = ["found", "merged", "entity", "scope", "time", "evidence"]
    print("## Sources against the truth set\n")
    print("| Source | Claim | " + " | ".join(columns) + " |")
    print("|---|---|" + "---|" * len(columns))
    for row in result["rows"]:
        cells = [
            "" if column not in row.cells else ("ok" if row.cells[column] else "FAIL")
            for column in columns
        ]
        print(f"| {row.file} | {row.claim} | " + " | ".join(cells) + " |")
    print()
    totals = {
        column: (
            sum(1 for row in result["rows"] if row.cells.get(column)),
            sum(1 for row in result["rows"] if column in row.cells),
        )
        for column in columns
    }
    print("Right / checked: " + ", ".join(f"{c} {a}/{b}" for c, (a, b) in totals.items()) + "\n")

    print("## Problems\n")
    for problem in result["problems"] or ["None."]:
        print(f"- {problem}")

    categories = ["earlier_mention", "shared_port", "no_id", "wrong_id", "control"]
    results = ["waited_right", "bound_right", "over_cautious", "confident_wrong", "no_claim", "error"]
    print("\n## Binding on the held-out set (numbers only)\n")
    print("| Category | Sources | " + " | ".join(results) + " | reason right |")
    print("|---|---|" + "---|" * len(results) + "---|")
    for category in categories:
        group = [d for d in decoys if d["category"] == category]
        counts = Counter(d["result"] for d in group)
        reasons = sum(1 for d in group if d.get("reason_right"))
        print(
            f"| {category} | {len(group)} | "
            + " | ".join(str(counts.get(name, 0)) for name in results)
            + f" | {reasons} |"
        )
    totals_decoys = Counter(d["result"] for d in decoys)
    print(
        f"\nConfidently wrong: {totals_decoys['confident_wrong']} of {len(decoys)}."
        f" These numbers describe this set of {len(decoys)} synthetic sources only."
    )

# Since AI 2026 BACKLOG

**The only list of open tasks.** An open task lives only here, including the owner's own non-code
actions. [`BUILD_INFO.json`](BUILD_INFO.json) tells the **state**, [`CHANGELOG.md`](CHANGELOG.md)
**what was done**, [`roadmap.md`](roadmap.md) **the order and the gates**,
[`DECISIONS.md`](DECISIONS.md) **the open decisions**.

**Rules:**
- A finished row is **removed** here and recorded in the CHANGELOG in the same session. Also when
  the owner did the work: on the owner's word that it is done, the row goes.
- Before listing a row as open, **verify** that it is not already done. An uncertain row is marked
  *check*, never left quietly open.
- A new open item never stays as a CHANGELOG sentence or a BUILD_INFO note alone.

**One boundary:** the preparation of the machines and connections for the event is tracked in the
Atlas artifact `SINCEAI-2026-SUUNNITELMA`, not here, because this repository is submitted.

Codes: **P** the owner's own actions, **REPO** the repository, **DOC** the documents to fill.

Updated 4.11.2026 (session 1: the list written with the scaffold).

---

## The owner's own actions

| Code | Task | Why / notes |
|---|---|---|
| P-1 | **Select the challenge** in sinceai.app. | Closes Friday 6.11. at 17:30 and is final ([`DECISIONS.md`](DECISIONS.md) row 1). |
| P-2 | **Read the chosen challenge's IP terms and data restrictions, and accept the IP terms** in sinceai.app. | Every team member accepts them in the app. Visibility and the license depend on them. |
| P-3 | **Submit** in sinceai.app: project details, submission URL, repository or demo link. | Closes Sunday 8.11. at 10:00 EET. Video and deck are optional. |

## The repository

| Code | Task | Why / notes |
|---|---|---|
| REPO-1 | **Rename the repository** after the selection (`gh repo rename <challenge>`) and update `BUILD_INFO.json` `github` and the name in `CLAUDE.md`. | GitHub redirects the old name. |
| REPO-2 | **Register the Atlas system** once the challenge is known, then render `docs/adr/` from its model. | Until then decisions live in [`DECISIONS.md`](DECISIONS.md). |
| REPO-3 | **Before any flip to public:** run gitleaks over the full history and read `CLAUDE.md` and `docs/` for anything internal. | Gitleaks was not installed on the main PC on 4.11.2026. Depends on [`DECISIONS.md`](DECISIONS.md) row 2. |

## Documents to fill

| Code | Task | Why / notes |
|---|---|---|
| DOC-1 | **Fill the README** (Challenge, Demo, Architecture diagram, How to run, Data and IP) and keep "AI tools used" current. | The submission points here. |
| DOC-2 | **Fill [`product.md`](product.md) and [`architecture.md`](architecture.md)** after the selection. | Both are stubs on purpose: no product decision is made before the event. |

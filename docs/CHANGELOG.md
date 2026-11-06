# Since AI 2026 CHANGELOG

Newest first. One entry per session; a session that ships several distinct things gets sub-entries.
What changed and *why*, with what was measured, so a later reader can tell a decision from a habit.
The canonical state is [`BUILD_INFO.json`](BUILD_INFO.json): refer to it, do not copy it here.

## Session 2, 6.11.2026: Elisa selected, decisions made, phases 0 and 1 built

**Why:** the challenge is selected and the decisions P1 to P6 are made, so the build starts from the
plan in the Atlas artifact `SINCEAI-2026-ELISA-RAKENNUSSUUNNITELMA`. The README, product,
architecture, roadmap, backlog and decisions now say so.

### Phase 4: the agent

**Built:** `claims_for` with three tiers from rules, the evidence template, the prohibition in code,
the agent reading counters itself from recent telemetry, `access_for`, the answer and gap logs, HTTP
endpoints, and `python -m app.ask`. The agent uses no model.

**Changed from the plan:**

- The check and action fields came now, not last. The tier and the next step read them, and the time
  allowed it. There is still no step machine. The unused `precondition` field is gone.
- Disagreement is in here already, not in phase 5, because an answer that ignored it would be wrong.
- A symptom is matched over the whole claim, not only its symptom field. The first try used the field
  alone and the agent could not find Elisa's advice, because "counters" and "zero" were in the check.
- For TRN-100 the plan expects a guess or no match. After 30.10. it can also find the VLAN finding from
  that unit, as `same_node` and `check_first`. Elisa's advice is still shown as not covering it, with
  the reported failure.

**Measured:** 122 tests pass with no key. The acceptance cases for the first three questions, the
barrier, the evidence wording and the prohibition pass, and so does most of the disagreement case.

**The result moves between runs.** Three runs of the same sources:

| Run | What differed | Truth set | Held-out: confidently wrong |
|---|---|---|---|
| 1 | First prompt | One miss, the truth set's own | 0 of 16 |
| 2 | Check and action fields added | None | 0 of 16 |
| 3 | A sentence about dashes added | One false success | 1 of 16 |

The prompt changed each time, so these are not clean repeats, and the cause of the change is not known.
The recorded answers are run 3, the newest: the best run was not picked. The false success was an
expert defending their advice, read as a report of trying it. A message that gives the advice no longer
counts as an outcome, which fixes the truth set's row with no new run. The rules were not changed for
the held-out result, and its files were not read, so it stands at 1 of 16.

### Phase 3: extraction and binding

**Built:** reading the sources, one structured model call per thread, binding by code from the graph,
merging, dating, evidence events, recorded answers, and scoring against both truth sets.

**Changed from the plan:**

- The model does not pick an entity even from candidates. It copies what the thread names, an
  identifier must literally be in the text, and code resolves it. This is stricter than the plan and
  cheaper to verify.
- Supersession and disagreement landed here instead of phase 5, because one model call reports them.
- Added two reasons a claim can wait, `unknown_id` and `contradicting_context`. `no_time` is not a
  reason to wait: a missing time never stopped a binding, so it stays an empty field.
- The teller key is computed per claim, so it cannot link one person across claims. That is what the
  decision promises, and a key per person would not have kept that promise.

**Measured,** with Claude Opus 5.5 through Anthropic's OpenAI compatibility layer. A structured reply
took 3.7 s on a one-line test. The numbers are `uv run python -m app.ingest --truth`:

- Truth set, 11 sources, first scored run: 10 right in every column. Found 11/11, merged 7/7, entity
  3/4, scope 4/4, time 7/7, evidence 5/6. The one miss was the truth set's own: the owner corrected it
  ([`DECISIONS.md`](DECISIONS.md) row 4), and the file says so. These numbers are from before that.
- Held-out set, 16 sources: 12 of 12 unclear cases waited with the right reason, 4 of 4 controls bound
  right, 0 confidently wrong. A small synthetic set written by a model of the same family: this says
  the rules are not obviously broken, not that they hold on real conversations.
- Without any key, the report is identical to the live run's, and 75 tests pass.

**Found by the first real call:** the model split Elisa's one piece of advice into two claims. The
prompt now says that advice for one problem is one claim. This came before the first full run.

### Phase 2: store and seed graph

**Built:** the SQLite schema with the seed graph, a JSON export, `/graph`, and `claims_for` as a
contract that answers "I don't know" with a reason and logs the answer and the gap.

**Decided while building:** the store is derived from `data/` and never committed, instead of shipping
a binary, so a clean install works and the repository stays diffable. The rules that matter most are
in the schema (a world time has a basis, a waiting claim has a reason), so a bug cannot quietly break
them. The teller key stays out of the export.

**Measured:** 31 tests pass. From an empty folder, `uv run python -m app.db --seed` builds 14 entities
and 7 edges; `claims_for("TRN-051", ...)` answers `unknown` with `no_claims` and names
`transmission-oncall`; `/graph` builds the store when it is missing and returns the same 14 and 7.

**Not tested:** the export has not been loaded into a graph database.

### Phase 0: skeleton

**Built:** Python 3.12, FastAPI and Uvicorn, with the model behind any OpenAI-compatible endpoint
through `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL`. These replace `SOMNUS_BASE_URL`, because the
product must run without the author's environment.

**Measured:** `uv run uvicorn app.api:app` starts and `/health` answers. Licences in the README were
read from the installed package metadata.

### Phase 1: data and truth set, before any rule

**Built:** Elisa's conversation and email unchanged, with their checksums under test; synthetic
sources, an event stream, counter series and a seed graph; the expected result for every source
(`expected_claims.json`); a held-out binding set from a separate agent. See
[`synthetic-data.md`](synthetic-data.md).

**Changed from the plan, because the plan could not run as written:**

- The two experts' disagreement moved from 25.10. to 2.11. Cases A1 and A5 expect the advice to be
  proposed and active on old units, and with the disagreement already known they would be disputed.
- A demo clock decides what is known, so each acceptance case runs at its own state of knowledge. A
  source is known once the clock has passed its `received_at`.
- The email's sentence about several cases is not evidence and never reaches the rendered evidence.
  Case A6 bans that word from the rendered text, and the word is in Elisa's own email.
- Added `config_changed` to the event types and a late counter rise on TRN-100, so a recovery caused
  by something else is not credited to the advice.
- The expert narrows the scope in the TRN-100 conversation ("the 4.x firmware ones"). Case A2 expects
  the answer to say what the teller said the advice covers, and nothing in the plan's data said so.

**Checked for phase 3:** Anthropic's OpenAI compatibility layer accepts `response_format` only as
`json_schema` with `strict: true`, rejects `temperature` below 1 on current models, and is described
as intended for testing and comparing rather than production. Read from the documentation on
6.11.2026, not tried: no key was available.

**A slip, left in the history:** commit `b523c43` says it adds the truth set but did not stage it.
`303f11d` adds it. No rule existed at either point, so the order holds.

## Session 1, 4.11.2026: the scaffold (commit 1, before the event)

**Why:** the organisers require pre-existing work to be kept apart from what is built at the event,
so the whole scaffold is one labelled commit and nothing else is committed before the event opens.

**Built:** the README skeleton with the plan's sections, `.gitignore`, `.gitattributes` (LF, because
the repository is created on Windows and run on a Mac), `.env.example`, an empty `.mcp.json`,
`CLAUDE.md` and the documentation structure of the sibling repositories (AvoQ, HomeTeam).

**Left out on purpose:** no copies of the Atlas source documents in `docs/history/` and no runbook,
because they hold maintenance instructions for machines and this repository is submitted. No
license, because the choice depends on the chosen challenge's IP terms. No CI until the build needs
a gate. No product content of any kind.

**Measured before the commit:** the folder was empty; the name `pkorrrhonen-cmd/sinceai-2026` was
free on GitHub; gitleaks is not installed on the main PC, so the check before the first push was
the staged file list and a pattern scan of the staged files. Gitleaks stays a gate before any flip
to public ([`BACKLOG.md`](BACKLOG.md) REPO-3).

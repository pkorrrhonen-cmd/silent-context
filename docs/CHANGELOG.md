# Since AI 2026 CHANGELOG

Newest first. One entry per session; a session that ships several distinct things gets sub-entries.
What changed and *why*, with what was measured, so a later reader can tell a decision from a habit.
The canonical state is [`BUILD_INFO.json`](BUILD_INFO.json): refer to it, do not copy it here.

## Session 2, 6.11.2026: Elisa selected, decisions made, phases 0 and 1 built

**Why:** the challenge is selected and the decisions P1 to P6 are made, so the build starts from the
plan in the Atlas artifact `SINCEAI-2026-ELISA-RAKENNUSSUUNNITELMA`. The README, product,
architecture, roadmap, backlog and decisions now say so.

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

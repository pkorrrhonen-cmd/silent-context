# Since AI 2026 CHANGELOG

Newest first. One entry per session; a session that ships several distinct things gets sub-entries.
What changed and *why*, with what was measured, so a later reader can tell a decision from a habit.
The canonical state is [`BUILD_INFO.json`](BUILD_INFO.json): refer to it, do not copy it here.

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

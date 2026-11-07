# Since AI 2026: notes for the build agent

An entry for the Since AI 2026 hackathon (6.11. to 8.11.2026), Elisa's challenge, selected on 6.11.
The build follows the Atlas artifact `SINCEAI-2026-ELISA-RAKENNUSSUUNNITELMA`, which implements the
decisions in [`docs/DECISIONS.md`](docs/DECISIONS.md). The repository
(`github.com/pkorrrhonen-cmd/silent-context`) is public since 7.11.2026, under the MIT licence.

## Where the truth is

| What | Where |
|---|---|
| What the jury reads | [`README.md`](README.md) |
| Product: for whom, what, what never | [`docs/product.md`](docs/product.md) |
| Architecture as prose | [`docs/architecture.md`](docs/architecture.md) |
| Open decisions, asked four at a time | [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| Architecture decision | [`docs/DECISIONS.md`](docs/DECISIONS.md) until the Atlas system exists, then the Atlas model, rendered into [`docs/adr/`](docs/adr/README.md) |
| State and the next session | [`docs/BUILD_INFO.json`](docs/BUILD_INFO.json): `state` and `next_session` |
| Open task | [`docs/BACKLOG.md`](docs/BACKLOG.md): the **only** list, including the owner's own actions |
| Order, event schedule and gates | [`docs/roadmap.md`](docs/roadmap.md) |
| What was done and measured | [`docs/CHANGELOG.md`](docs/CHANGELOG.md), newest first |
| Lesson paid for | [`docs/LESSONS.md`](docs/LESSONS.md): the root cause as the heading, the rule at the end |
| Machines, connections, recovery | Atlas `SINCEAI-2026-RUNBOOK`, never this repository |
| Working practice | this file |

Nothing goes into two places as a copy; a reference is enough. There is no SEED document.

## Golden rules

- **Commit 1 is the scaffold made before the event; everything after it is built at the event.**
  The organisers require pre-existing work to be kept apart, and the README's sentence says so.
  Nothing else is committed before the event opens. A change that cannot wait gets a commit of its
  own labelled pre-existing, and the same commit changes the README's sentence to name it.
- **Endpoints come from environment variables only,** never hard-coded. `.env.example` lists each.
- **No secrets in the repository.** `git diff --staged` before every commit.
- **The main AI tools are recorded** in the README's "AI tools used", in the same commit as the
  first work they did.
- **The repository is submitted, so operations stay out of it.** Home machines, SSH, tunnels and
  recovery commands live in Atlas. No internal address, user name or key file path enters git.
- **Public, so every commit is read by strangers.** The flip was made on 7.11.2026 after gitleaks over
  the full history and a read of the documents for anything internal; `.gitleaks.toml` says what is
  allowed to look like a secret. Run gitleaks again before any commit that adds data or configuration.
- **Each challenge's rules, licences and data restrictions apply** to everything built here.

## Working practice

- **Measure before claiming.** A claim about a service, a library's behaviour or a platform's limit
  is checked. A negative result is a result.
- **Proposals as what / why / impact.** The owner decides. Two equally good options: both shown,
  one recommended.
- **Decision boxes** (Atlas artifact `SUNRISE-TYOTAPA-PAATOSLAATIKOT`). Collect the list in
  `docs/DECISIONS.md`, ask four at a time, record each answer in the file before the next batch.
- **No codes in conversation with the owner.** BACKLOG codes are document structure; in conversation
  things are named. A status report in three parts: done, to decide, open.
- **Git.** `main` on GitHub is the only truth. During the event work goes straight to `main` in small
  commits; there is no CI gate unless one is added. Never force-push or rewrite history: the history
  is the evidence of what was built at the event. Destructive git commands are always asked. Commit
  subject: what changed and why, in English.
- **Dependencies by permission:** "X is needed for Y. Options A, B. Recommend A because Z."
- **Language.** Code, comments, commits and documentation in English, because the repository is
  submitted. Conversation with the owner in Finnish.
- **Formatting.** No em dashes or en dashes. Author name in documents: Petri Korhonen.
- **Commands for the owner** are copy-paste ready, one per code block. The main PC's shell is
  PowerShell 5.1 (no `&&`, no nested quotes); at the event the machine is the Mac.
- **Where work runs.** Anything that needs the local model server (`LLM_BASE_URL` pointed at it) runs
  in Claude Code on the Mac. A cloud session reaches only Atlas and the repository.
- **Atlas** is read and written through the claude.ai connector. `.mcp.json` is deliberately empty,
  as in the sibling repositories: a set Authorization header blocks the OAuth fallback.

## Session start

1. **Sync before the first edit:**
   ```bash
   git fetch origin
   ```
   ```bash
   git rev-list --left-right --count origin/main...HEAD
   ```
2. **Read** `docs/BUILD_INFO.json` `next_session` (`read_first`, `scope`, `gate`).
3. **Decisions:** which rows of `docs/DECISIONS.md` are still open.
4. **Atlas:** once the system exists, `atlas_get_workspace("<system>")`. Until then the source is the
   artifact `SINCEAI-2026-ELISA-TILANNE`, which says what is done, what was measured and what waits.

## Session end

The session is done when the next one can start from a clean desk.

1. **Documents:** `BUILD_INFO.json` (`state`, `next_session`), `CHANGELOG.md` (what was done and
   measured), `BACKLOG.md` (done rows out, new rows in, the owner's too), `DECISIONS.md` (every answer
   recorded), `LESSONS.md` if a lesson was paid for, the README's "AI tools used" if a tool was added.
2. **Atlas:** once the system exists, a new architecture decision enters the Atlas model first and is
   rendered into `docs/adr/`, and the session writes `<system>.STATUS` (read the newest first).

## Layout

| Path | What |
|---|---|
| `app/` | The product code |
| `tests/` | The tests |
| `data/` | Elisa's examples, synthetic sources and events, the seed graph, the truth set |
| `docs/` | The documentation above |
| `docs/adr/` | Rendered decisions, once the Atlas system exists |
| `docs/history/` | Empty on purpose; its README says why |
| `.env.example` | The environment variables, no values that are secrets |

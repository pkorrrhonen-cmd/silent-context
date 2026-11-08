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

Codes: **P** the owner's own actions, **REPO** the repository, **DOC** the documents to fill,
**BUILD** the build's phases.

Updated 8.11.2026 (session 6: the event is over, third in Elisa's top three; the vote window closed).

---

## The owner's own actions

| Code | Task | Why / notes |
|---|---|---|
| P-12 | **After the event, decide whether the hosted copy stays up.** `cd hosting && npx wrangler delete` takes the Worker and its container down; [`hosting.md`](hosting.md) says how the image is removed too. | The copy at `https://silent-context.pkorrrhonen.workers.dev` sleeps two hours after the last visit and costs nothing asleep; awake it costs about 0.03 USD an hour beyond the plan's included amounts. The Sunday cron wakes it 08:00 to 13:55 Finnish time every week until the Worker is deleted or the `triggers` line in `hosting/wrangler.jsonc` goes. |
| P-8 | **On the main PC,** point the checkout at the renamed repository: `git remote set-url origin https://github.com/pkorrrhonen-cmd/silent-context.git`. | GitHub redirects the old name, so this can wait; it only keeps the remote honest. |

## The repository

| Code | Task | Why / notes |
|---|---|---|
| REPO-2 | **Register the Atlas system,** then render `docs/adr/` from its model. | Not during the event weekend (the owner, 6.11.2026). Until then decisions live in [`DECISIONS.md`](DECISIONS.md). |

## The build

| Code | Task | Why / notes |
|---|---|---|
| BUILD-8 | **Present the slides,** if ever asked. | Phase 8. The video is final (7.11. late evening, v6: the owner's voice, 176 s, the light look, captions in the band); the owner uploads it (P-10). The slides exist (7.11.): [`slides/silent-context.pptx`](slides/silent-context.pptx), twelve slides with speaker notes in the light look, and the PDF beside it as a supporting document; the five-picture deck is the pitch deck (P-3). A change to the words: [`slides/build/`](slides/build/) or [`slides/five/`](slides/five/), then rebuild. If a finalist: the page itself on the arrow keys is the stage presentation (four minutes, live), the five pictures the backup. |

## Documents to fill

| Code | Task | Why / notes |
|---|---|---|
| DOC-2 | **Finish [`architecture.md`](architecture.md)** as components come to exist. | Data flow and threats are still open. |

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

Updated 7.11.2026 (session 4, evening).

---

## The owner's own actions

| Code | Task | Why / notes |
|---|---|---|
| P-10 | **Upload the video to YouTube as unlisted** (the owner's choice, 7.11.: only those with the link can watch) and open the link once in a private window. | The builders' guide (read 7.11.): YouTube is the only accepted format, public or unlisted, no MP4 or WebM upload. The file is `silent-context-v4-captions.mp4` (135 s, narration v4: the pause on the whole view after the pitch, the cards timed to the voice, a second of the whole view before each zoom) in the Desktop folder "Silent context submission V3". The older folders hold the v3 cut (118 s) and the first cut (127 s) as fallbacks. The title, description and steps are in the V3 folder's `submission-notes.md`. |
| P-3 | **Submit** in sinceai.app. | The form opens Saturday 7.11. at 18:00 EET and closes Sunday 8.11. at 10:00; the owner sends on Saturday evening, by 09:30 at the latest, and a submission can be edited after sending. The package is the Desktop folder "Silent context submission V3": every field's text is in its `submission-notes.md` (the tagline, 128 of 140 characters, the About text, Built with, the GenAI answer); the five-picture deck `silent-context-in-five.pdf` goes in as the pitch deck, the full deck as a supporting document, the zip as the source. Rebuild the zip with `git archive` if main moves after the last rebuild. The older folders "Silent context submission V2" and "Silent context submission" are the earlier packages, kept as fallbacks. |
| P-11 | **Vote** in sinceai.app on Sunday 10:00 to 12:00. | 20 pairwise comparisons per builder; the vote picks the finalists and feeds the company top three. Can be done from anywhere. The closing ceremony at 13:15 needs presence only from the five finalists, who must be at the stage side at 13:00 and present live. |
| P-8 | **On the main PC,** point the checkout at the renamed repository: `git remote set-url origin https://github.com/pkorrrhonen-cmd/silent-context.git`. | GitHub redirects the old name, so this can wait; it only keeps the remote honest. |
| P-7 | *Optional:* **ask Elisa's representative the questions** in the Atlas artifact `SINCEAI-2026-ELISA-PAATOKSET` part 1.5, face to face, if there is time. | Saturday at the showroom, until 18:00. No decision depends on the answers. |

## The repository

| Code | Task | Why / notes |
|---|---|---|
| REPO-2 | **Register the Atlas system,** then render `docs/adr/` from its model. | Not during the event weekend (the owner, 6.11.2026). Until then decisions live in [`DECISIONS.md`](DECISIONS.md). |

## The build

| Code | Task | Why / notes |
|---|---|---|
| BUILD-8 | **Present the slides,** if ever asked. | Phase 8. The video is final (7.11., the owner's voice, 127 s, captions in the band); the owner uploads it (P-10). The slides exist (7.11.): [`slides/silent-context.pptx`](slides/silent-context.pptx), ten slides with speaker notes, and the PDF beside it, which goes into the submission as the pitch deck (P-3). A change to the words: [`slides/build/`](slides/build/), then rebuild. |

## Documents to fill

| Code | Task | Why / notes |
|---|---|---|
| DOC-2 | **Finish [`architecture.md`](architecture.md)** as components come to exist. | Data flow and threats are still open. |

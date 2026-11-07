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

Updated 7.11.2026 (session 3).

---

## The owner's own actions

| Code | Task | Why / notes |
|---|---|---|
| P-3 | **Submit** in sinceai.app: project details, submission URL, repository or demo link, video, source zip. | Closes Sunday 8.11. at 10:00 EET; the plan is to send by 09:30. |
| P-10 | **Put the final video where the submission can point** (YouTube unlisted, or the file as the form allows) and open the link once logged out. | The video is final on 7.11.: `silent-context-en-captions.mp4` in the Desktop folder "Silent context video" and in the pipeline's media folder. |
| P-8 | **On the main PC,** point the checkout at the renamed repository: `git remote set-url origin https://github.com/pkorrrhonen-cmd/silent-context.git`. | GitHub redirects the old name, so this can wait; it only keeps the remote honest. |
| P-7 | *Optional:* **ask Joni the questions** in the Atlas artifact `SINCEAI-2026-ELISA-PAATOKSET` part 1.5, face to face, if there is time. | Saturday at the Joki showroom, 9 to 12 and 14.30 to 18. No decision depends on the answers. |

## The repository

| Code | Task | Why / notes |
|---|---|---|
| REPO-2 | **Register the Atlas system,** then render `docs/adr/` from its model. | Not during the event weekend (the owner, 6.11.2026). Until then decisions live in [`DECISIONS.md`](DECISIONS.md). |
| REPO-3 | **Before any flip to public:** run gitleaks over the full history and read `CLAUDE.md` and `docs/` for anything internal. | Depends on [`DECISIONS.md`](DECISIONS.md) row 2. gitleaks is not installed on the Mac; a pattern scan of the history on 7.11. found no key. |
| REPO-4 | **Build the source zip with `git archive`,** not from the working folder. | The working folder holds untracked leftovers that are not part of the product. |

## The build

| Code | Task | Why / notes |
|---|---|---|
| BUILD-8 | Video and slides. | Phase 8. The video is final (7.11., the owner's voice, 127 s, captions in the band); the owner places it for the submission (P-10). The slides have an outline in [`slides.md`](slides.md); the owner makes the deck. |

## Documents to fill

| Code | Task | Why / notes |
|---|---|---|
| DOC-1 | **Read the README once more before the submission** and keep "AI tools used" current. | The submission points here. The diagram and "What was tested" went in on 7.11. |
| DOC-2 | **Finish [`architecture.md`](architecture.md)** as components come to exist. | Data flow and threats are still open. |

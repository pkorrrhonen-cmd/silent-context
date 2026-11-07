# Since AI 2026 CHANGELOG

Newest first. One entry per session; a session that ships several distinct things gets sub-entries.
What changed and *why*, with what was measured, so a later reader can tell a decision from a habit.
The canonical state is [`BUILD_INFO.json`](BUILD_INFO.json): refer to it, do not copy it here.

## Session 4, 7.11.2026: the submission's rules, and the work read as a judge

**Why:** the build is done; what remained was how the video is handed in, what Sunday asks of the
owner, and whether the work reads well to a judge and to an ordinary viewer. Nothing in `app/`,
`web/`, `data/` or the slides changed.

**The builders' guide** (sinceai.ai/hackathon-2026/guide/builders, read 7.11. evening):

- The submission is made in sinceai.app only, by Sunday 8.11. 10:00 EET, and can be edited after
  sending. The video must be a public or unlisted **YouTube link; no video file is accepted.** This
  settles the backlog's open question (P-10).
- The form's fields: challenge, project name (80 characters), tagline (140), About (5,000), Built
  with, repository link, YouTube link, one source zip (100 MB), MLH questions including the GenAI
  tools, challenge terms; optional demo URL, one pitch deck (PDF, PPT or PPTX) and two supporting
  documents. The one-line description drafted on 7.11. was 254 characters, so a 128-character tagline
  was written. The PDF goes in as the deck, because voters open it from the vote card.
- Sunday: 10:00 deadline; 10:00 to 12:00 a participant vote of 20 pairwise comparisons per builder;
  12:00 five finalists, the highest-ranked from five different company challenges; 13:15 the closing
  ceremony at EduCity; 13:30 the company top three; 14:00 the finals, live only, four minutes and six
  of questions. Presence is needed only from finalists. The vote is the owner's new action (P-11).

**Read as a judge and as an ordinary viewer:** the README, the narration, the ten scenes in the
browser, the slide text and the Desktop folder's notes. The page's scene stories, the 22 second
pitch and the limits scene carry the idea; the README answers Elisa's three asks in its own
"Demo" section and says what was measured and what was not. Found and recorded, not changed: the
page is dense at a glance and is best read through the video; slides 4 and 8 are text-heavy; the
README has no picture of the page, so a reader on GitHub sees prose and a diagram only. The
repository and its raw README answer 200 without a login; the zip holds the same 133 files as the
tracked tree.

**Changed:** the Desktop folder's `submission-notes.md` now holds every field's text in the form's
order, the YouTube steps, Sunday's timetable and the zip's rebuild command. The backlog's P-10 is
the YouTube upload, P-3 points at the notes, P-11 is the vote, and DOC-1 (read the README before
the submission) is done. The source zip was rebuilt from this session's last commit.


### The second half of session 4: a picture in the README, a Finnish paper, and a proposal for the video

**Built:** the README's "Demo" section now opens with a picture of the page at scene 4
(`docs/images/page-scene-4-use.png`, 1600 by 900, shot from the running page with headless Chrome as the
slides were), because a reader on GitHub saw prose and a diagram only. The one console line during the
shot was the favicon's 404. A Finnish plain-language paper for the owner, "Silent context selkokielellä",
is in the Desktop folder "Silent context suomeksi" as HTML and PDF: the story, the three steps, the example
on the demo's clock, what it never does, what is real and what is simulated, a glossary from our words to
everyday ones, how to read the page, the video scene by scene, and a thirty second explanation. It is the
owner's working paper, not part of the submission, and not in the repository.

**Proposed, not built:** a second cut of the video on a plain-language narration, `video/narration-v3.md`
(297 words, 111 s): an animated story in front, four page scenes zoomed on the panel that matters, a short
montage of the doubt cases, the limits as a card. The options and the recommendation are decision 18 in
[`DECISIONS.md`](DECISIONS.md), open for the owner; the 7.11. video stays the fallback. The source zip was
rebuilt from this session's last commit.

### The second cut of the video, built on the owner's choice A

**Why:** decision 18. The first cut was correct but dense for a viewer new to it; the owner chose a new cut on
a plain-language narration, with the first cut as the fallback.

**Built:** `video/narration-v3.md` (twelve blocks, 305 words, the sentences the owner voiced from
`narration-read-v3.txt`), `video/story.html` (four cards in the page's look: the chat and "It lives in one chat",
the four steps, the limits, the close; each element arrives on a schedule that follows the narration),
`video/scenes_v3.py` (the take: two cards, the page's scenes 2 to 9 zoomed toward the panel the sentence is
about, two cards; the zoom is a transform on the page's body that the recorder injects, so the product's page
is not changed), `cut_from_take.py` now names clips from the narration's headers and takes `--prefix`, and
`v3-cut.json` and `v3-final.json` with a 0.6 s tail.

**Measured:**

- **The zoom records smoothly without `will-change`.** With `will-change: transform` on the body the
  screencast gave 4 frames during a 0.6 s move; without it a frame every 17 ms, 73 frames in a 1.2 s move.
  The first ten second trial showed the answer panel cut at both sides at 1.6 times, so the zoom now fits the
  target to the frame: the answer panel's whole width fits at 1.38, its left three quarters at 1.6, the claim
  card at 1.8. Scene 2 opens Elisa's thread over the whole frame, so that block has no zoom.
- **The take:** 149.2 s, 1757 screencast frames; the cards' animations and their end states are in it (a
  ticker repaints the page five times a second, so the end of a move is never dropped).
- **The owner's track:** 107.8 s from ElevenLabs; the aligner found all twelve blocks at the default
  threshold, 3.46 words per speech second, fit cost 1.48; the only slow sentences are the close's two.
- **The final:** `silent-context-v3-captions.mp4`, 117.6 s, 1920 by 1080, H.264 and AAC, 12.7 MB with the
  captions burned into the band (10.6 MB without), 36 caption cues; frames read at six points. The guide-voiced
  draft before it, 124.4 s, was the pipeline check; `final.py --narration` needs an absolute path, a relative
  one is read from the working folder and fails.

**Where it is:** the Desktop folders "Silent context submission" (beside the first cut, with the notes pointing
at the second) and "Silent context video", and the pipeline's media folder. The owner watches both cuts and
picks the one to upload.

### The submission package V2 and the deck in five pictures

**Why:** the owner wants a whole new package with the new files, and a short deck from which the thing opens
with about five pictures, for the pitch deck field that voters open from the vote card.

**Built:** the Desktop folder "Silent context submission V2": the second cut and its captions, the source zip
from main's tip, the ten-slide deck and its PDF, the notes rewritten for the package, and
`silent-context-in-five.pdf`: five pages of 1920 by 1080 in the page's look, written as `docs/slides/five/five.html`
and rendered with headless Chrome (`render.js`), with crops of the running page read from its own elements at
device scale 2 (`shoot.js`, `shots/`). The pages: the chat and "It lives in one chat"; the four steps; the agent's
answer with the device record; the three doubt cases; what was measured and the limits. Every number on
the fifth page is the README's. The notes now send the five-picture deck as the pitch deck and the full deck
as a supporting document. The first package stays in "Silent context submission" as the fallback.

**Measured:** the PDF is five pages, 0.66 MB, each page read as a PNG; the only fix was the closing line,
which wrapped.

## Session 3, 7.11.2026: the technical check before the checkpoint

**Why:** the owner saw the page the evening before and holds phase 6's checkpoint. Before anything
is built on it, the session checked that the demo and the repository are technically sound and that
the build still follows the product and the plan. Nothing in `app/`, `web/` or `data/` changed.

**Measured:**

- 150 tests pass in the working folder.
- **A clean install passed** (phase 7's A10, listed as untried until now): `git archive HEAD` into an
  empty folder, `uv sync`, `.env` copied from `.env.example` with its values empty, and every command
  in the README's "How to run" in order, with no key. 150 tests pass there too. The seed builds 14
  entities and 7 edges. Ingest reads 11 sources into 5 claims from the recorded answers, and with
  `--until 2026-10-20T12:00:00` 5 sources into 2 claims. The truth report is clean: found 11/11,
  merged 7/7, entity 4/4, scope 4/4, time 7/7, evidence 6/6, no problems; held-out 1 of 16
  confidently wrong, the same as the recorded run. `ask demo`, `ask claims` and `ask access` answer
  as the README says, and the export writes `export/graph.json`. `--refresh` without a key stops
  with the message that names the settings, instead of failing somewhere deeper.
- **All ten scenes ran at 1440 by 900 with the browser pane visible:** no console errors, every
  request answered 200, and the dimming between scenes was seen moving (a 0.35 s transition, caught
  mid-way in a screenshot). This closes the one thing session 2 could not check. The Ask button sits
  inside the viewport at that size. Rebuilding the store for a scene takes 0.05 s.
- **No key in the history:** a pattern scan of every commit's diff found nothing. gitleaks is not
  installed on the Mac either, so the gate before any flip to public still needs it
  ([`BACKLOG.md`](BACKLOG.md) REPO-3).

**Against the plan:** everything on the plan's "never cut" list exists and runs. Of the cutting
order, the "mark as wrong" button, the MCP wrapper, the Cypher export and the transcript were left
out, in that order, as the plan allows; the procedure fields, the point-in-time query, the
disagreement and the held-out metric are in. The README still lacks the architecture diagram and
the "what was tested" section, and `docs/what-is-simulated.md` does not exist (DOC-1, DOC-3).

**Open after this:** the owner's checkpoint on the page and the captions, the product name, and
phase 7's remaining half, the acceptance table for the slides.

### The session's end

Main is at `dfd83fa`, 37 commits, pushed; gitleaks over the full history and the working tree finds
nothing. Two folders on the owner's Desktop have one role each: "Silent context submission" holds
exactly what the form takes (the final video, the deck and its PDF as in main, the source zip from
main's tip, `submission-notes.md`), and "Silent context video" holds the video's working files (the
drafts, the owner's track, the SRT files, the reading copy); the stale copies of the zip and the deck
were removed from it. Open after this session: the owner's two actions, P-10 and P-3, and after the
event REPO-2 and P-8.

### The slides

**Built:** `docs/slides/silent-context.pptx`, ten slides from [`slides.md`](slides.md) in the page's own look:
its colours, Calibri for text and Consolas for identifiers, slide 1 the cover and the problem in one, as the
video's first card. Written by a script (`docs/slides/build/`, pptxgenjs, not part of the product) so that a
change to the words is a change to one file and a rebuild. Four slides carry the page itself, taken from the
running demo with headless Chrome at 1600 by 900 and device scale 2: the fourth scene whole, the claim and graph
panels of the third, the claim panel alone, and the agent's answer of the fourth. Speaker notes on every slide,
from the outline and the narration. A PDF beside it, `silent-context.pdf`.

**Measured:** every sentence and number was read against the README's "What was tested", `acceptance.md`,
`what-is-simulated.md`, `product.md` and the narration's last block; the one difference from the outline is 154
tests, not 152 ([`DECISIONS.md`](DECISIONS.md) rows 15 to 17). The file passes the OOXML validator with no
finding. Every slide was rendered and looked at: the first render overflowed the thread panel on slide 1 and
the picture on slide 3, and three titles wrapped into their content; fixed, rendered again, clean. The ten
screenshots gave one console error, the missing favicon. PowerPoint on the Mac first answered no Apple event
within two minutes, an automation permission waiting on the owner, so the PDF was first LibreOffice's export
(installed for this with Homebrew, with Office's Calibri and Consolas loaded into a throwaway profile). Once the
owner granted the permission, the PDF was exported from PowerPoint itself: ten pages, Calibri and Consolas, the
same layout. A folder on the Desktop, "Silent context submission", holds the final video, the deck, its PDF, the
source zip rebuilt from main's tip and `submission-notes.md`, what goes where in the form. The zip was checked as
before: 133 files, the same list as `git ls-files`, no `.env`, store or database inside; unpacked into an empty
folder with `.env` from `.env.example`, `uv sync`, 154 tests pass, the seed builds 14 entities and 7 edges, and
`ask demo` answers.

### The source zip

Built from main with `git archive --format=zip --prefix=silent-context/ HEAD` at `c9bfe7f`, into the
owner's Desktop folder "Silent context video", 251 kB. Measured: 127 files, the same number as `git
ls-files`, no `.env`, store or database inside. Unpacked into an empty folder with `.env` copied from
`.env.example` and nothing filled in: `uv sync`, 154 tests pass, `ask demo` answers, the export writes
`graph.json` and `graph.cypher`, and gitleaks finds nothing in it.

### Public, under MIT

**Decided by the owner** ([`DECISIONS.md`](DECISIONS.md) rows 2 and 3): the repository goes public now
that the video is final, under the MIT licence.

**Measured before the flip:** gitleaks 8.30.1, installed for this, over all 30 commits of every branch
and over the working tree. It first reported 56 findings in the history and 28 in the tree, all one
thing: the `key` field at the top of every recorded answer in `data/extractions/`, the SHA-256 of the
prompt that a clean install looks the answer up by (`app/extract.py`), 64 hex characters in all 28
files and in no file anything else. Allowed in `.gitleaks.toml` with the reason; both scans then
report no leaks. A pattern search of the tracked text found only `127.0.0.1` and token counts, the
history never held a `.env`, a key file or a database, and the Neo4j throwaway password is nowhere in
it. `CLAUDE.md` and `docs/` were read for anything internal: one private individual's first name in
the backlog became "Elisa's representative". Then `LICENSE` and the licence in `pyproject.toml`, the
README's IP section, the flip with `gh repo edit`, and the check: GitHub reports the repository public
with the MIT licence detected, and the page and the raw README answer 200 to an anonymous request.

### The final video, on the owner's voice

The owner recorded the twelve blocks in ElevenLabs from the reading copy and handed the track over
in the Desktop folder (an MP3 of 114.6 s, mono, 44.1 kHz). Measured: `align.py` found every block
boundary in a real pause at the default threshold, fit cost 0.90 (the guide track's 0.67), 3.59
words a speech second. `cut_from_take.py` cut the twelve clips to his speech, 127.0 s of picture,
and `final.py` built `silent-context-en.mp4` and `silent-context-en-captions.mp4`: 127.2 s, 1920 by
1080, the captions in the band, 7.6 MB with captions, with the SRT files beside them. Frames at 2,
9, 21, 40, 60 and 116 seconds checked: the cards bright for their holds, the page under the band,
nothing covered. The files are in the pipeline's media folder and in the owner's Desktop folder
"Silent context video". In the video the page appears at 22 seconds and "use" starts at 53, inside
the owner's rule of 20 and about 60.

### The pitch, the captions' band and the MCP wrapper

**Decided by the owner** ([`DECISIONS.md`](DECISIONS.md) rows 11 to 14): the larger-text picture is
approved as a pre-version; the captions go into a black band of their own under the picture, because
the frame holds many views and text; a very concise pitch of about 20 seconds goes in front (the
problem, how it is solved), so that Elisa's representative first grasps what the solution does and then
sees it as a technical solution; the MCP wrapper is included; the owner produces the final voice in
ElevenLabs and hands it over for alignment.

**Built:**

- **The band.** The take is recorded as a 1920 by 950 picture (`--scale 1.2`, the page at 1600 by
  792 CSS pixels, checked to fit without scrolling) and the plan adds a 130 pixel black band under it,
  so the video is 1920 by 1080 and the burned captions sit in the band, white on black, two lines of
  45 pixels. The pipeline learned this in its own repository (`sf3d-ai-lab` `6b86ab0`: a `band` in the
  plan or `--band`, and any even frame size for the picture). Measured on frames at 3, 15, 44 and 70
  seconds: nothing of the page is covered.
- **The pitch.** Two cards in the page's own look (`video/pitch.html`), recorded in the same take as
  the page: the problem, with Erkki's own answer from Elisa's file beside it, and the answer as three
  steps (read as written, tied to the network, one call for the agent). Narration v2: blocks 01 and 02
  are the pitch, 60 words over 22 seconds; the earlier overview block over the page went, so the page
  itself starts at 22 seconds and the viewer reaches "use" at 68. Twelve blocks, 356 words, 131
  seconds planned; the guide track aligned with fit cost 0.67. The draft with the pitch and the band
  is `silent-context-en-guide-band-captions.mp4`, 135.8 s, 8.2 MB. The owner accepted the pitch's words
  and cards as they are, so the narration is final for his voice.
- **A lesson paid for** ([`LESSONS.md`](LESSONS.md)): the first take's first card stayed dim, because
  the screencast dropped the last frame of its fade. The cards cut in hard now.
- **The MCP wrapper** (`app/mcp_server.py`, the `mcp` package 2.3.0): `claims_for`, `access_for` and
  `source` as tools over stdio, each the function behind the HTTP interface, so an answer is the same
  whichever way it is asked and no model runs. Tested over an in-memory transport (the three tools
  listed, the same tier and next step as the direct call, a file outside the manifest refused) and as
  a real stdio process started by a client. 154 tests pass. The README says how a client starts it.

### The checkpoint, and the page rebuilt for clarity

**Decided by the owner** ([`DECISIONS.md`](DECISIONS.md) rows 6 to 10): the IP terms were accepted at
selection; the product is Silent context, and the repository was renamed `silent-context`; the
repository goes public as soon as it is fit to open, with gitleaks then; the Cypher export and the Neo4j
trial are done because the build is ahead; the video makes the whole idea clear in 20 seconds and
fully grasped at about 60. The checkpoint's verdict on the page: confusing at first glance.

**Built, for clarity.** The structure stays (the time axis, three panels, the agent, ten scenes), and
what competed for attention went:

- Each scene opens with a title, two sentences on what happens and where to look, instead of one
  ellipsised line. The scene buttons keep short names.
- Field names left the screen: a source has a readable name from the manifest, a claim is named by
  what it advises (bounce, SFP first, check port, key), a match level and an action kind are said in
  words, a waiting claim says why in words, and the time axis says "from 14.10. · still believed
  true" instead of `valid_from` and `valid_to`.
- The evidence template is shown one line per row, the label apart from what it says. The text is the
  template's, unchanged: nothing is added, so the decision on evidence still holds.
- The sources list says "not yet received", "Elisa's file, unchanged", "one claim" or "no advice in
  it"; the numbers beside it are sentences.

**Measured:** 151 tests pass. All ten scenes ran again at 1440 by 900 with no console errors, and the
Ask button fits the viewport.

### Phase 7: the acceptance table

**Built:** `app/accept.py` runs the build plan's cases on the recorded data, at each case's clock, with
no key, and writes [`acceptance.md`](acceptance.md): one row per case with what was asked, what the
plan expects, what was observed and the result. The checks are the ones in `tests/test_claims.py`; the
table exists so the result fits on a slide. A9 reports numbers and is not a pass or a fail; A10 is the
clean install, done by hand and quoted. A test runs the table and fails on any failing row.

**Measured:** 20 computed rows, 20 hold; 152 tests pass. One lesson paid for on the way: the first
run locked SQLite, because the script kept several connections to one store open while an answer's
log sat unwritten in one of them. One connection at a time fixed it; the tests had hidden this by
closing after each case.

### Phase 8, started: the video's words and picture

**Built:** `video/narration.md`, one block per scene in the form the pipeline's aligner parses, to the
owner's rule: the whole idea in the first 20 seconds (block 01, over the agent proposing), how it
happens by about 66 seconds, the harder cases and the limits after that, 129 seconds and 351 words in
all, 2.4 to 2.9 words a second per block. `video/scenes.py` drives the page through its own `goTo()`
and reads each hold from the narration, so the two cannot drift apart. `video/cut_from_take.py` writes the cut list and the
final plan from a take's marks and the alignment, each clip as long as its speech. The pipeline is
pre-existing work in another repository; the video folder is the event's.

**Measured, the first picture:** the recorder (Edge through Playwright, 1920 by 1080) drove the page
through its eleven blocks in one take of 160 seconds, every block mark where the scenes file put it. A
guide track from the Mac's own speech aligned to all eleven blocks (fit cost 0.58, faster than the
planned pace at 3.6 words a second). The first draft ran 159 seconds, because every clip played its
whole hold; cut to the speech, the guide-voiced draft with burned captions is 132 seconds, 1920 by
1080, H.264 and AAC, 9.4 MB (`media/silent-context/final/silent-context-en-guide-captions.mp4` in
the pipeline's repository, outside git). A second take at 1.2 device pixels per CSS pixel lays the page out at 1600 by 900, its
own height, and its text reads a fifth larger; its draft is `silent-context-en-guide-large-captions.mp4`,
132 seconds, 9.9 MB, and it is the recommendation. Both drafts went to the owner, who has not seen them
yet. One trap on the way: the pipeline's `assemble.py --out` is relative to its `--media` folder, so a
path given as if relative to the shell landed under `media/media/`, and the first "large" build silently
used the first take's clips. The byte sizes being identical gave it away.

### Documents

`docs/what-is-simulated.md` says what is real, what stands in and what is not built on purpose. The
README now has the architecture diagram (Mermaid, rendered by GitHub) and a "What was tested" section
pointing at the table and the numbers.

### Cypher export and a Neo4j trial

**Built:** `app/export.py` writes `export/graph.cypher` beside the JSON. Sources and evidence events
become nodes of their own, because a property cannot hold a list of maps; an evidence event with a
unit points at it. A test holds that every entity, the claim, its source and its evidence appear, that
a quote inside a text is escaped, and that the teller key is absent.

**Measured** against the official `neo4j:5` container on the Mac (Docker Desktop started for it):
every statement ran with no edits. The database held 5 Claim, 14 Entity, 14 Evidence and 9 Source
nodes and ten relationship types (ABOUT 8, HAS_EVIDENCE 14, ON 12, FROM_SOURCE 9, LOCATED_AT 3,
INSTANCE_OF 3, APPLIES_TO 1, CONFLICTS_WITH 1, SUPERSEDES 1, HAS_BARRIER 1). A query over the graph
alone found the claim seen on TRN-042, the same-class unit TRN-051, and reported successes on both.

## Session 2, 6.11.2026: Elisa selected, decisions made, phases 0 and 1 built

**Why:** the challenge is selected and the decisions P1 to P6 are made, so the build starts from the
plan in the Atlas artifact `SINCEAI-2026-ELISA-RAKENNUSSUUNNITELMA`. The README, product,
architecture, roadmap, backlog and decisions now say so.

### Phase 6: the page

**Built:** one page with ten scenes on the arrow keys: a live time axis in the form of Elisa's layer
picture, sources with their checksums, claims, the graph, the agent and the numbers on extra work. A
source opens as it was read. The endpoints behind it are `/state`, `/clock` and `/source`, and `/source`
opens only files in the manifest.

**Changed from the plan:**

- The graph is hand-made SVG instead of vis-network. Laid out by kind, it stays still on a recording,
  and it adds no dependency or licence. The decision allowed any drawing.
- System fonts, because the page must not fetch anything from outside and a font would have been one
  more thing to vendor.
- The simulated "mark as wrong" button is left out, first in the plan's cutting order.

**Measured:** 150 tests pass with no key. All ten scenes ran in a browser at 1440 by 900 with no console
errors, and the page was also opened at 1920 by 1080. One thing could not be checked: the browser pane
was hidden and did not finish CSS transitions, so the dimming between scenes was checked by its classes
and has not been seen moving.

The zero conversations started on the page has a test behind it: nothing in `app/` except the model
client imports anything that can reach outside.

### Phase 5: events, ageing, disagreement

**Built:** the firmware recheck per claim and unit, the status for an order that cannot be told, a rise
in counters recorded apart from anyone's explanation, and the log line "the agent proposed, a person
did, the outcome", filled from device events. The agent's logs now carry over when the store is rebuilt
at a later clock.

**Measured:** 136 tests pass with no key, and the truth set has no problems, including the rise on
TRN-100 that came after a configuration change and is not credited to the advice.

**Repeats of the held-out set,** with the prompt unchanged and no rule tuned to them
(`data/truth/held_out_repeats.json`). The recorded answers come from this same prompt, which makes six
runs:

| Confidently wrong, of 16 | Runs |
|---|---|
| 0 | 3 |
| 1 | 3 |

In the five repeats the wrong binding was the same one file each time, in the category of an identifier
that looks clear but is wrong. So this is not random scatter: there is one kind of trap the model
sometimes walks into, and code does not catch it. That file has not been read and no rule was changed
for it, so the set stays honest. The five repeats took 80 model calls, 354,025 input and 40,549 output
tokens, about 2.23 USD at list price.

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

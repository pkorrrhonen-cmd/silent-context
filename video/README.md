# The video

The pipeline is pre-existing work in another repository (`sf3d-ai-lab/video`); the commands are in the Atlas
artifact `SINCEAI-2026-VIDEO`. What is here was written at the event. Two cuts exist: the first (7.11. afternoon,
narration v2) and the second (7.11. evening, narration v3, decision 18), both on the owner's voice.

## The second cut, v3

| File | What |
|---|---|
| `narration-v3.md` | The narration, twelve blocks in plain words, one per picture, in the aligner's form. |
| `narration-read-v3.txt` | The same as plain paragraphs, which the owner read into ElevenLabs. |
| `story.html` | Four story cards in the page's look: the chat and "It lives in one chat", the four steps, the limits, the close. Each card's elements arrive on a schedule that follows the narration, and a tiny ticker repaints the page five times a second so the screencast always carries the end of a move. |
| `scenes_v3.py` | The recorder's scene: the two cards, the page's scenes 2 to 9, the two cards. The page is zoomed toward the panel the sentence is about by a transform on its body that the recorder injects (`ZOOM_JS`); the product's page is not changed. `zoomtest` and `zoomtest2` are the trials that measured the zoom. |
| `v3-cut.json`, `v3-final.json` | The assembly and the final plan for the second cut, written by `cut_from_take.py`; the plan's `tail` is 0.6 s. |

Measured 7.11.: with `will-change: transform` on the body the screencast gave 4 frames during a 0.6 s move;
without it, a frame every 17 ms (73 frames in a 1.2 s move), so the move is smooth and the text stays crisp. A
panel is zoomed only as far as it fits the frame: the answer panel's whole width fits at 1.38 times, its left
three quarters at 1.6; the claim card at 1.8.

## The first cut, v2

| File | What |
|---|---|
| `narration.md` | The narration, one block per scene, in the aligner's form. Blocks 01 and 02 are the pitch. |
| `pitch.html` | The two pitch cards in front of the page, in the page's own look: the problem, then the answer. |
| `narration-read.txt` | The same narration as plain paragraphs, which the owner read into ElevenLabs. |
| `scenes.py` | The recorder's scene: the two cards, then the page's ten scenes in the narration's order, each held. |
| `cut.json`, `final.json` | The assembly and the final plan of the first cut. |

## Shared

| File | What |
|---|---|
| `cut_from_take.py` | Writes a cut list and a final plan from a take's marks and the alignment, each clip as long as its speech; the clips are named from the narration's block headers, and `--prefix` keeps two cuts' files apart. Rerun after a new take or a new voice. |

The page must be running (`uv run uvicorn app.api:app`; the recorder takes its address with `--stage`). The take
is recorded with `--size 1920x950 --scale 1.2`: a picture of 1920 by 950, and under it a black band of 130 pixels
that the plan's `band` adds, so the video is 1920 by 1080 and the burned captions sit in the band, never over the
page (the owner, 7.11.2026). At scale 1.2 the page is laid out at 1600 by 792 CSS pixels, checked to fit without
scrolling, and its text reads a fifth larger than at scale 1. The pipeline's `assemble.py --out` and
`final.py --clips` are relative to `--media`, so a second set of clips is `--out cut-v3` and `--clips cut-v3`.

The order of the pipeline, from the Atlas artifact: record the take with the scene file, make a guide track from
the narration with the Mac's speech and align it, write the plans with `cut_from_take.py`, assemble, and build a
guide-voiced draft with `--burn` for the owner to approve. The owner's own voice from ElevenLabs comes last: align
his track, rerun `cut_from_take.py` so each clip is as long as his speech, assemble, and build the final with the
same plan. For the second cut, in order:

```bash
uv run python pipeline/record.py --stage http://127.0.0.1:8000/ --scenes <repo>/video/scenes_v3.py --out ../media/silent-context/takes-v3 --size 1920x950 --scale 1.2 demo
```

```bash
uv run python pipeline/align.py <repo>/video/narration-v3.md ../media/silent-context/audio/narration.wav --out ../media/silent-context/audio/scenes.json
```

```bash
python3 video/cut_from_take.py --media ~/projects/sf3d-ai-lab/media/silent-context --take takes-v3/demo --narration video/narration-v3.md --scenes-json audio/scenes.json --prefix v3- --name silent-context-v3
```

```bash
uv run python pipeline/assemble.py <repo>/video/v3-cut.json --media ../media/silent-context --out cut-v3
```

```bash
uv run python pipeline/final.py <repo>/video/v3-final.json --media ../media/silent-context --clips cut-v3 --burn
```

For a guide run, `final.py` takes `--narration` as an absolute path (a relative one is read from the working
folder and fails), `--scenes-json` relative to `--media`, and its own `--name`.

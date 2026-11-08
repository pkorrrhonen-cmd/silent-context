# The video

The pipeline is pre-existing work in another repository (`sf3d-ai-lab/video`); the commands are in the Atlas
artifact `SINCEAI-2026-VIDEO`. What is here was written at the event. Two cuts exist: the first (7.11. afternoon,
narration v2) and the second (7.11. evening, narration v3, then v4 after the owner watched it, then v5 expanded on
decision 19, then v6: the v5 words and voice on the light look, decision 24), both on the owner's voice.

## The second cut, v3 and v4

| File | What |
|---|---|
| `narration-v5.md` | The narration the final uses: sixteen blocks in plain words, one per picture, in the aligner's form. v5 adds the policy letting the agent act, any source in any language, and the question drafted for a person, and the close names what was left out on purpose. |
| `narration-read-v5.txt` | The same as plain paragraphs, which the owner read into ElevenLabs. |
| `narration-v4.md`, `narration-v3.md` and their read texts | The words of the earlier finals (135 s and 118 s), kept for the record. |
| `story.html` | Four story cards in the page's look: the chat and "It lives in one chat", the four steps, the limits, the close. Each element's moment comes from the voice: `data-cue="S,F"` is sentence S of the block and a fraction of its length, and `storyGo(n, cues)` sets the delays from the aligned track; without cues the `data-at` seconds are used. A tiny ticker repaints the page five times a second so the screencast always carries the end of a move. |
| `scenes_story.py` | The recorder's scene (was `scenes_v3.py`): the two cards, the page's scenes 1 to 12, the two cards. The page is zoomed toward the panel the sentence is about by a transform on its body that the recorder injects (`ZOOM_JS`); the product's page is not changed. Every zoomed block first holds the whole view for a second. In the page block `videoFocus` lights each part as the voice names it (the panels the way the page lights a scene's, the clock with an outline). With `SILENT_CONTEXT_ALIGNMENT` pointing at align.py's output, the cards, the focus moments and the later moves take their moments from the voice, so the take is recorded after the voice is aligned. `zoomtest` and `zoomtest2` are the trials that measured the zoom. |
| `v3-cut.json`, `v4-cut.json`, `v5-cut.json`, `v6-cut.json` and the `-final.json` beside each | The assembly and the final plan of each final, written by `cut_from_take.py`; the plan's `tail` is 0.6 s. v6 is a new take of the v5 words on the same aligned voice, after the page, the cards and the decks went light (decision 24); nothing in the narration or the alignment changed, so `align.py` was not rerun. |

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

## The vertical video for the owner's own channels

Made 7.11.2026 late evening, after the submission was sent; not part of the submission (the form is closed, the
owner). A 9:16 video of 1080 by 1920, under 60 seconds, for Instagram, LinkedIn and the like: what was built at the
event, told to someone who knows nothing about the subject, in the owner's voice. The storyboard was agreed scene by
scene with the owner before the build (a first 30 second cut of six cards, built before that, stays in the history).

| File | What |
|---|---|
| `narration-social.md` | Seven blocks, 180 words, in the aligner's form; `narration-read-social.txt` is what the owner reads into ElevenLabs. |
| `social.html` | One stage for the seven scenes, laid out for the portrait frame: every word inside x 60 to 940 and y 230 to 1270, the burned captions from 1290 to 1440 (`final.py --captions social`), the band under them left to the platforms' buttons. The owner's two photos from the event (scene 1), the map of Finland with the network as dots and links (scenes 2 to 6), Elisa's Teams thread as in the example file (scene 4), the advice as a note that flies to its unit (5), a fault far north and the agent's real answer from the page (6), the close (7). `storyGo(n, cues)` starts scene n and times every move from the aligned voice; `window.videoInstant` jumps to a scene's end state for checking. |
| `social/finland.js` | The map: Finland's outline from Natural Earth 1:50m (public domain), 49 towns as the units and each one's two nearest neighbours as the links; an illustration, and named so on screen. |
| `social/answer-scene-4.png` | The agent's answer at scene 4, shot from the running page at two times the size and cropped, 7.11.2026, named and dated on screen. |
| `scenes_social.py` | The recorder's scene: the seven scenes in order, each at its block's mark, the moves timed from the aligned voice (`SILENT_CONTEXT_ALIGNMENT`). |
| `social-cut.json`, `social-final.json` | Written by `cut_from_take.py --band 0 --tail 0.8`: no band, the captions sit over the picture in the safe area; a shorter tail after each block's last word, because with the default 1.2 s the final was 61.2 s against the owner's limit of 60. |

The two photos are the owner's and stay out of the repository: the page reads them from the pipeline's media folder
beside this checkout (`../../sf3d-ai-lab/media/silent-context/photos/`), so the take is recorded on the Mac only.

In order, from `sf3d-ai-lab/video`: the guide track (`guide.py`) and its alignment first, the take with the
alignment set, then `cut_from_take.py --band 0 --tail 0.8 --prefix social-`, `assemble.py --out cut-social` and
`final.py --clips cut-social --burn --captions social`. The owner's voice last: align it (`--noise=-38dB`), record the
take again on that alignment, and run the same three steps. The guide cut (70 s on the Mac's slow voice) is never
published. The final on the owner's voice (7.11. evening, his track 53.6 s): 58.4 s, 1080 by 1920, 7.7 MB with the
captions burned in, 5.8 MB without, in the Desktop folder "Silent context social video".

```bash
SILENT_CONTEXT_ALIGNMENT=../media/silent-context/audio/scenes-social.json uv run python pipeline/record.py --stage "file://<repo>/video/social.html" --scenes <repo>/video/scenes_social.py --out ../media/silent-context/takes-social --size 1080x1920 social
```

Measured 7.11.: a layer that waits at opacity 0 is not painted before its fade, and the first fade of the 2000 pixel
photo had a 0.67 s gap in the screencast; at opacity 0.002 it is painted and the fade has its frames. The note's
flight animated its width and font size in the first take and stalled 0.43 s; by transform alone it does not.

### The result cut (8.11.2026 evening)

After the result (third in Elisa's own top three) the video was made again, a little over a minute, with the result
in its first twenty seconds and the thanks at its end. The storyboard and the words were approved by the owner before
the build. The same stage, with two scenes added and the close changed; the first video's files stay as they are.

| File | What |
|---|---|
| `narration-social-v2.md` | Nine blocks, 234 words, in the aligner's form; `narration-read-social-v2.txt` is what the owner reads into ElevenLabs. |
| `social-v2.html` | The first stage's scenes plus the result (the "Build complete" screen, then the results board as a band pushed in on the third-place line, the owner's photos from the closing ceremony) and the thanks (the stage under "Thank you", then the map at rest with every unit green); the close names the place. The push-in is a transform about the cell's centre, carried to the frame's middle, so the screencast keeps its frames. |
| `scenes_social_v2.py` | The recorder's scene: `scenes_social.py` pointed at the nine blocks and the second stage. |
| `social-v2-cut.json`, `social-v2-final.json` | Written by `cut_from_take.py --band 0 --tail 0.5 --prefix social-v2-`. |

The three new photos (`build-complete.jpg`, `results-board.jpg`, `closing-stage.jpg`) are the owner's and stay out of
the repository, in the pipeline's media folder beside the first two; the stage photo carried an EXIF rotation, which
ffmpeg applied when scaling it. The owner's voice was aligned first (72.4 s, 4.1 words a second, fit cost 0.29), the
take recorded on it, then the same three steps as above. Measured on the take: four stalls of 0.27 to 0.38 s, each
at a crossfade between a full-frame photo and the map or at a block's end, none inside a move. The final: 77.8 s,
1080 by 1920, 15.7 MB with the captions burned in, 12.3 MB without, in the Desktop folder "Silent context social
video V2".

The plan's `narration` must be the track meant: `cut_from_take.py --audio audio/narration-social-v2.wav` writes it (the
default is the submission video's `audio/narration.wav`, and the first delivery of this cut carried that voice). After
any change to the track or the plan, `final.py` needs `--force`: it keeps the normalised track and the encoded scenes
in `final/work/<name>` and otherwise reuses them. The sound is checked before delivery by aligning the final's own
audio to the narration (`align.py` on the audio extracted from the mp4): each block within 0.1 s of the track's.

```bash
SILENT_CONTEXT_ALIGNMENT=../media/silent-context/audio/scenes-social-v2.json uv run python pipeline/record.py --stage "file://<repo>/video/social-v2.html" --scenes <repo>/video/scenes_social_v2.py --out ../media/silent-context/takes-social-v2 --size 1080x1920 social
```

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
same plan. For the second cut the voice comes first, because the take follows it; in order:

```bash
uv run python pipeline/align.py <repo>/video/narration-v5.md ../media/silent-context/audio/narration.wav --out ../media/silent-context/audio/scenes.json
```

```bash
SILENT_CONTEXT_ALIGNMENT=../media/silent-context/audio/scenes.json uv run python pipeline/record.py --stage http://127.0.0.1:8000/ --scenes <repo>/video/scenes_story.py --out ../media/silent-context/takes-v5 --size 1920x950 --scale 1.2 demo
```

```bash
python3 video/cut_from_take.py --media ~/projects/sf3d-ai-lab/media/silent-context --take takes-v5/demo --narration video/narration-v5.md --scenes-json audio/scenes.json --prefix v5- --name silent-context-v5
```

```bash
uv run python pipeline/assemble.py <repo>/video/v5-cut.json --media ../media/silent-context --out cut-v5
```

```bash
uv run python pipeline/final.py <repo>/video/v5-final.json --media ../media/silent-context --clips cut-v5 --burn
```

For a guide run, `final.py` takes `--narration` as an absolute path (a relative one is read from the working
folder and fails), `--scenes-json` relative to `--media`, and its own `--name`.

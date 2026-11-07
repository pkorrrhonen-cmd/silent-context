# The video

The pipeline is pre-existing work in another repository (`sf3d-ai-lab/video`); the commands are in the Atlas
artifact `SINCEAI-2026-VIDEO`. What is here was written at the event:

| File | What |
|---|---|
| `narration.md` | The narration, one block per scene, in the aligner's form. Blocks 01 and 02 are the pitch; the owner voices it last. |
| `pitch.html` | The two pitch cards in front of the page, in the page's own look: the problem, then the answer. |
| `scenes.py` | The recorder's scene: the two cards, then the page's ten scenes in the narration's order, each held. |
| `cut.json` | The assembly: twelve clips cut from the one take by its block marks, nothing sped up. |
| `final.json` | The final plan: each narration scene over its clip, the sentences starting 0.3 s in, the captions in a band. |
| `cut_from_take.py` | Writes both of the above from a take's marks and the alignment, each clip as long as its speech. Rerun after a new take or a new voice. |

The page must be running at `http://127.0.0.1:8000` (`uv run uvicorn app.api:app`). The take is recorded with
`--size 1920x950 --scale 1.2`: a picture of 1920 by 950, and under it a black band of 130 pixels that the plan's
`band` adds, so the video is 1920 by 1080 and the burned captions sit in the band, never over the page (the
owner, 7.11.2026: the frame holds many views and text). At scale 1.2 the page is laid out at 1600 by 792 CSS
pixels, checked to fit without scrolling, and its text reads a fifth larger than at scale 1. The pipeline's
`assemble.py --out` and `final.py --clips` are relative to `--media`, so a second set of clips is `--out cut-band`
and `--clips cut-band`, nothing longer.

The order of the pipeline, from the Atlas artifact: record the take with `scenes.py`, make a guide track from
`narration.md` with the Mac's speech and align it, write the plans with `cut_from_take.py`, assemble with
`cut.json`, and build a guide-voiced draft with `final.json --burn` for the owner to approve. The owner's own
voice from ElevenLabs comes last: align his track, rerun `cut_from_take.py` so each clip is as long as his
speech, assemble, and build the final with the same plan.

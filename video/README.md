# The video

The pipeline is pre-existing work in another repository (`sf3d-ai-lab/video`); the commands are in the Atlas
artifact `SINCEAI-2026-VIDEO`. What is here was written at the event:

| File | What |
|---|---|
| `narration.md` | The narration, one block per scene, in the aligner's form. The owner voices it last. |
| `scenes.py` | The recorder's scene: walks the page's scenes in the narration's order and holds each. |
| `cut.json` | The assembly: eleven clips cut from the one take by its block marks, nothing sped up. |
| `final.json` | The final plan: each narration scene over its clip, the sentences starting 0.3 s in. |

The page must be running at `http://127.0.0.1:8000` (`uv run uvicorn app.api:app`). The recorder's browser
window is 1920 by 1080, so the page is laid out as at that size.

The order of the pipeline, from the Atlas artifact: record the take with `scenes.py`, assemble with `cut.json`,
make a guide track from `narration.md` with the Mac's speech, align, and build a guide-voiced draft with
`final.json` for the owner to approve the picture. The owner's own voice from ElevenLabs comes last and
replaces the guide track in the same plan.

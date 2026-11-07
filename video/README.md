# The video

The pipeline is pre-existing work in another repository (`sf3d-ai-lab/video`); the commands are in the Atlas
artifact `SINCEAI-2026-VIDEO`. What is here was written at the event:

| File | What |
|---|---|
| `narration.md` | The narration, one block per scene, in the aligner's form. The owner voices it last. |
| `scenes.py` | The recorder's scene: walks the page's scenes in the narration's order and holds each. |
| `cut.json` | The assembly: one clip from the take, nothing sped up. |

The page must be running at `http://127.0.0.1:8000` (`uv run uvicorn app.api:app`). The recorder's browser
window is 1920 by 1080, so the page is laid out as at that size.

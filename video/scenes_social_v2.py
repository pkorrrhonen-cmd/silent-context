"""The result cut of the 9:16 social video (narration-social-v2.md, social-v2.html): the same scene as scenes_social.py,
pointed at the nine blocks and the second stage.

    SILENT_CONTEXT_ALIGNMENT=../media/silent-context/audio/scenes-social-v2.json uv run python pipeline/record.py --stage about:blank --scenes <this file> --out ../media/silent-context/takes-social-v2 --size 1080x1920 social

Written at the event's end, after the result; the pipeline itself is pre-existing work.
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("scenes_social", HERE / "scenes_social.py")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
# The scene reads these module globals when it runs, so the first stage's constants are replaced here.
_base.NARRATION = HERE / "narration-social-v2.md"
_base.CARDS = HERE / "social-v2.html"
_base.BLOCKS = [f"{i:02d}" for i in range(1, 10)]

SCENES = {"social": _base.social}

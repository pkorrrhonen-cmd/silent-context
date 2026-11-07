"""The page's scenes for the video recorder (sf3d-ai-lab, pipeline/record.py).

    uv run python pipeline/record.py --stage http://127.0.0.1:8000/ --scenes <this file> --out ../media/silent-context/takes demo

One take, `demo`, walks the page's scenes in the order of narration.md and holds each for its block's
seconds plus a margin, so the aligner has picture to cut to. The seconds come from narration.md next to
this file, so the two cannot drift apart. The page is driven through its own goTo(), so a take is the
same every time. Written at the event; the pipeline itself is pre-existing work.
"""

import asyncio
import re
from pathlib import Path

NARRATION = Path(__file__).with_name("narration.md")
# Narration block to page scene index: block 01 shows the agent proposing (scene 4), then the scenes in order.
BLOCK_TO_SCENE = {
    "01": 3, "02": 0, "03": 1, "04": 2, "05": 3, "06": 4, "07": 5, "08": 6, "09": 7, "10": 8, "11": 9,
}
MARGIN = 2


def seconds_per_block() -> dict[str, int]:
    text = NARRATION.read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^## (\d\d) · [^·]+ · (\d+) s · \d+ words", text, re.M)}


async def demo(page, cap, args) -> None:
    seconds = seconds_per_block()
    missing = set(BLOCK_TO_SCENE) - set(seconds)
    if missing:
        raise SystemExit(f"narration.md has no block for {sorted(missing)}")
    await page.wait_for_selector("#story-title")
    for block, scene in BLOCK_TO_SCENE.items():
        await page.evaluate(f"goTo({scene})")
        # The page keeps `busy` true while a scene loads; the overlay and the answer arrive within a second.
        await page.wait_for_function("() => typeof busy !== 'undefined' && !busy")
        await asyncio.sleep(0.6)
        cap.mark(f"block {block}")
        await asyncio.sleep(seconds[block] + MARGIN)
    cap.mark("done")


SCENES = {"demo": demo}

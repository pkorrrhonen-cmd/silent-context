"""The video's scenes for the recorder (sf3d-ai-lab, pipeline/record.py).

    uv run python pipeline/record.py --stage http://127.0.0.1:8000/ --scenes <this file> --out ../media/silent-context/takes --size 1920x950 --scale 1.2 demo

`--size 1920x950` leaves a band of 130 pixels under the picture for the captions (final.py --band, in
final.json), so they never cover the page (the owner, 7.11.2026). `--scale 1.2` lays the page out at 1600 by
792 CSS pixels in it, checked to fit without scrolling, with text a fifth larger than at scale 1, which
read small on 7.11.2026.

One take, `demo`: the two pitch cards of pitch.html first (narration.md blocks 01 and 02), then the page's
scenes in the narration's order, each held for its block's seconds plus a margin, so the aligner has picture
to cut to. The seconds come from narration.md next to this file, so the two cannot drift apart. The cards and
the page are driven through their own pitchGo() and goTo(), so a take is the same every time. Written at the
event; the pipeline itself is pre-existing work.
"""

import asyncio
import re
from pathlib import Path

NARRATION = Path(__file__).with_name("narration.md")
PITCH = Path(__file__).with_name("pitch.html")
# Narration block to pitch card: the problem, then the answer.
BLOCK_TO_CARD = {"01": 0, "02": 1}
# Narration block to page scene index: the page's ten scenes in order.
BLOCK_TO_SCENE = {"03": 0, "04": 1, "05": 2, "06": 3, "07": 4, "08": 5, "09": 6, "10": 7, "11": 8, "12": 9}
MARGIN = 2


def seconds_per_block() -> dict[str, int]:
    text = NARRATION.read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^## (\d\d) · [^·]+ · (\d+) s · \d+ words", text, re.M)}


async def demo(page, cap, args) -> None:
    seconds = seconds_per_block()
    missing = (set(BLOCK_TO_CARD) | set(BLOCK_TO_SCENE)) - set(seconds)
    if missing:
        raise SystemExit(f"narration.md has no block for {sorted(missing)}")
    await page.goto(PITCH.resolve().as_uri())
    await page.wait_for_selector("body[data-ready='1']")
    await asyncio.sleep(1)
    for block, card in BLOCK_TO_CARD.items():
        await page.evaluate(f"pitchGo({card})")
        await asyncio.sleep(0.6)
        cap.mark(f"block {block}")
        await asyncio.sleep(seconds[block] + MARGIN)
    await page.goto(args.stage)
    await page.wait_for_function("() => typeof goTo === 'function' && typeof busy !== 'undefined'")
    await asyncio.sleep(1)
    for block, scene in BLOCK_TO_SCENE.items():
        await page.evaluate(f"goTo({scene})")
        # The page keeps `busy` true while a scene loads; the overlay and the answer arrive within a second.
        await page.wait_for_function("() => !busy")
        await asyncio.sleep(0.6)
        cap.mark(f"block {block}")
        await asyncio.sleep(seconds[block] + MARGIN)
    cap.mark("done")


SCENES = {"demo": demo}

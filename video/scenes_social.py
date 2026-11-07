"""The 9:16 social cut's scene for the recorder (sf3d-ai-lab, pipeline/record.py): the six cards of social.html, one
per block of narration-social.md, each shown at its block's mark with its elements timed from the aligned voice.

    SILENT_CONTEXT_ALIGNMENT=../media/silent-context/audio/scenes-social.json uv run python pipeline/record.py --stage about:blank --scenes <this file> --out ../media/silent-context/takes-social --size 1080x1920 social

The cards are a file of their own, laid out for 1080 by 1920 with every word inside the platforms' safe area
(VIDEO-RULEBOOK.md §9); the recorder opens it from disk, so --stage is not used. The take is recorded after the voice
is aligned, as scenes_story.py's cards are: each card's elements take their moments from the aligned track's sentence
times; without SILENT_CONTEXT_ALIGNMENT the fixed seconds in social.html are used. Written at the event, after the
submission was sent; the pipeline itself is pre-existing work.
"""

import asyncio
import json
import os
import re
from pathlib import Path

NARRATION = Path(__file__).with_name("narration-social.md")
CARDS = Path(__file__).with_name("social.html")
BLOCKS = ["01", "02", "03", "04", "05", "06"]
MARGIN = 2
# The voice starts 0.3 s into each clip (the final plan), and the clip starts at the block's mark, which follows the
# card's first frame by a frame or two.
VOICE_OFFSET = 0.35


def seconds_per_block() -> dict[str, int]:
    text = NARRATION.read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^## (\d\d) · [^·]+ · (\d+) s · \d+ words", text, re.M)}


def cues_per_block() -> dict[str, list[list[float]]]:
    """Each block's sentences as [start, end] seconds from the block's first frame, from the aligned track; {} without one."""
    path = os.environ.get("SILENT_CONTEXT_ALIGNMENT")
    if not path:
        print("  no SILENT_CONTEXT_ALIGNMENT: the cards use their fixed seconds", flush=True)
        return {}
    aligned = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    first = {s["scene"]: s["start"] for s in aligned["scenes"]}
    out: dict[str, list[list[float]]] = {}
    for s in aligned["sentences"]:
        t0 = first[s["scene"]]
        out.setdefault(s["scene"], []).append([round(s["start"] - t0 + VOICE_OFFSET, 2), round(s["end"] - t0 + VOICE_OFFSET, 2)])
    print(f"  cues from {path}: {len(out)} blocks", flush=True)
    return out


async def social(page, cap, args) -> None:
    """One take: the six cards in order, each held for its block's seconds and a margin."""
    seconds = seconds_per_block()
    cues = cues_per_block()
    missing = [b for b in BLOCKS if b not in seconds]
    if missing:
        raise SystemExit(f"{NARRATION.name} has no block for {missing}")
    await page.goto(CARDS.resolve().as_uri())
    await page.wait_for_selector("body[data-ready='1']")
    # No card until its block, so a clip never starts on the frame before its card has painted.
    await page.evaluate("storyGo(-1)")
    await asyncio.sleep(1)
    for i, block in enumerate(BLOCKS):
        c = json.dumps(cues[block]) if block in cues else "null"
        await page.evaluate(f"storyGo({i}, {c})")
        # Two animation frames, so the card has painted and the screencast has a frame of it before the mark.
        await page.evaluate("new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))")
        cap.mark(f"block {block}")
        print(f"    block {block}: card {i}, held {seconds[block] + MARGIN} s", flush=True)
        await asyncio.sleep(seconds[block] + MARGIN)
    cap.mark("done")


SCENES = {"social": social}

"""The second cut's scenes for the recorder (sf3d-ai-lab, pipeline/record.py): story cards and the page zoomed.

    uv run python pipeline/record.py --stage http://127.0.0.1:8000/ --scenes <this file> --out ../media/silent-context/takes-v3 --size 1920x950 --scale 1.2 demo

Same frame and scale as scenes.py (a 1920 by 950 picture, the captions' band under it, the page laid out at 1600 by
792 CSS pixels). New here: the page is zoomed toward the one panel the narration talks about, by a transform on
the page's body that the recorder injects (ZOOM_JS); the product's page is not changed. `zoomtest` is the ten
second trial of that zoom, recorded before anything else was built (decision 18). Written at the event; the
pipeline itself is pre-existing work.
"""

import asyncio
import re
from pathlib import Path

NARRATION = Path(__file__).with_name("narration-v3.md")
STORY = Path(__file__).with_name("story.html")
MARGIN = 2

# Injected once per page load. videoZoom(selector, k, ms): translate and scale the body so the panel sits in the
# middle of the frame at k times its size, clamped so the frame never shows anything outside the page. The panel's
# place is read from the offset chain, which a transform does not affect, so a zoom can follow a zoom.
ZOOM_JS = """
(() => {
  const body = document.body;
  if (!body.dataset.zoomInit) {
    body.dataset.zoomInit = "1";
    body.style.transformOrigin = "0 0";
    document.documentElement.style.overflow = "hidden";
  }
  window.videoZoom = (sel, kmax, ms, pad, rect) => {
    ms = ms === undefined ? 600 : ms; pad = pad === undefined ? 24 : pad; rect = rect || [0, 0, 1, 1];
    body.style.transition = ms ? `transform ${ms}ms cubic-bezier(.3,.7,.2,1)` : "none";
    if (!sel) { body.style.transform = ""; return; }
    const el = document.querySelector(sel);
    if (!el) throw new Error("videoZoom: no element " + sel);
    let x = 0, y = 0;
    for (let e = el; e && e !== body; e = e.offsetParent) { x += e.offsetLeft; y += e.offsetTop; }
    let w = el.offsetWidth, h = el.offsetHeight;
    x += rect[0] * w; y += rect[1] * h; w *= rect[2]; h *= rect[3];
    const W = window.innerWidth, H = window.innerHeight;
    const k = Math.min(kmax, (W - pad) / w, (H - pad) / h);
    const cx = x + w / 2, cy = y + h / 2;
    let tx = W / 2 - k * cx, ty = H / 2 - k * cy;
    tx = Math.min(0, Math.max(W - k * W, tx));
    ty = Math.min(0, Math.max(H - k * H, ty));
    body.style.transform = `translate(${tx.toFixed(1)}px, ${ty.toFixed(1)}px) scale(${k.toFixed(3)})`;
    return {sel, k: +k.toFixed(3), x, y, w, h, W, H};
  };
})();
"""


def seconds_per_block() -> dict[str, int]:
    text = NARRATION.read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^## (\d\d) · [^·]+ · (\d+) s · \d+ words", text, re.M)}


async def open_page(page, args) -> None:
    await page.goto(args.stage)
    await page.wait_for_function("() => typeof goTo === 'function' && typeof busy !== 'undefined'")
    await page.evaluate(ZOOM_JS)
    await asyncio.sleep(1)


async def scene(page, index: int) -> None:
    await page.evaluate(f"goTo({index})")
    await page.wait_for_function("() => !busy")


async def zoom(page, sel, k: float = 1.6, ms: int = 600, rect=(0, 0, 1, 1)):
    """Zoom toward sel, or toward a part of it (rect: left, top, width, height as fractions of the element), at up to
    k times; the helper lowers k so that part fits the frame. None zooms out."""
    return await page.evaluate(f"videoZoom({sel!r}, {k}, {ms}, 24, {list(rect)})" if sel else f"videoZoom(null, 1, {ms})")


# The blocks on the story cards, and the blocks on the page: scene index, then the moves (at seconds after the
# block's mark, the target, the zoom, the part of the target). The answer's left three quarters hold the badge, the
# step and the first facts; the rest is cut at the frame's edge as a camera would.
CARD = {"01": 0, "02": 1, "11": 2, "12": 3}
ANSWER = (0, 0, .86, .75)   # the badge, the step and the first facts; a long "why this unit" is cut at the edge
WIDE = (0, 0, 1, .75)       # the whole width, for an answer whose step runs over two lines
PAGE = {
    "03": (1, []),  # the page opens Elisa's thread over the whole frame; it is the picture, read as written
    "04": (2, [(0.4, "#claims", 1.8, (0, 0, 1, 1)), (9.6, "#timeline", 1.8, (.3, .5, .5, .5))]),
    "05": (3, [(0.4, "#answer", 1.7, ANSWER)]),
    "06": (4, [(0.4, "#answer", 1.7, (0, 0, .8, .9))]),
    "07": (5, [(0.4, "#answer", 1.7, WIDE)]),
    "08": (6, [(0.4, "#answer", 1.7, (0, 0, 1, .9))]),
    "09": (7, [(0.4, "#answer", 1.7, WIDE)]),
    "10": (8, [(0.4, "#answer", 1.7, WIDE)]),
}
MOVE_MS = 900


async def cards(page, cap, seconds, blocks) -> None:
    await page.goto(STORY.resolve().as_uri())
    await page.wait_for_selector("body[data-ready='1']")
    await asyncio.sleep(1)
    for block in blocks:
        await page.evaluate(f"storyGo({CARD[block]})")
        await asyncio.sleep(0.3)
        cap.mark(f"block {block}")
        await asyncio.sleep(seconds[block] + MARGIN)


async def demo(page, cap, args) -> None:
    """One take: two story cards, the page's scenes zoomed, two story cards."""
    seconds = seconds_per_block()
    missing = (set(CARD) | set(PAGE)) - set(seconds)
    if missing:
        raise SystemExit(f"{NARRATION.name} has no block for {sorted(missing)}")
    await cards(page, cap, seconds, ["01", "02"])
    await open_page(page, args)
    for block in sorted(PAGE):
        index, moves = PAGE[block]
        await zoom(page, None, 1, 0)
        await scene(page, index)
        await asyncio.sleep(0.6)
        cap.mark(f"block {block}")
        t = 0.0
        for at, sel, k, rect in moves:
            await asyncio.sleep(at - t)
            t = at
            fit = await zoom(page, sel, k, MOVE_MS, rect)
            print(f"    {block}: {sel} x{fit['k']}", flush=True)
        await asyncio.sleep(seconds[block] + MARGIN - t)
    await zoom(page, None, 1, 0)
    await cards(page, cap, seconds, ["11", "12"])
    cap.mark("done")


async def zoomtest(page, cap, args) -> None:
    """Ten seconds: scene 4, zoom to the answer, then to the claims, then back."""
    await open_page(page, args)
    await scene(page, 3)
    await asyncio.sleep(1.5)
    cap.mark("answer")
    await zoom(page, "#answer", 1.6)
    await asyncio.sleep(4)
    cap.mark("claims")
    await zoom(page, "#claims", 1.7)
    await asyncio.sleep(3)
    cap.mark("back")
    await zoom(page, None)
    await asyncio.sleep(2)
    cap.mark("done")


async def zoomtest2(page, cap, args) -> None:
    """The same, with a 1200 ms move, to count the screencast's frames during the move; prints each target's fit."""
    await open_page(page, args)
    await scene(page, 3)
    await asyncio.sleep(1.5)
    cap.mark("answer")
    print("  ", await zoom(page, "#answer", 1.8, 1200), flush=True)
    await asyncio.sleep(3)
    cap.mark("claims")
    print("  ", await zoom(page, "#claims", 1.8, 1200), flush=True)
    await asyncio.sleep(3)
    cap.mark("back")
    await zoom(page, None, 1, 1200)
    await asyncio.sleep(2)
    cap.mark("done")


SCENES = {"demo": demo, "zoomtest": zoomtest, "zoomtest2": zoomtest2}

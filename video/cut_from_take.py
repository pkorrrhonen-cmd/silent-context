"""Write the cut list and the final plan from a take's marks and the aligned narration.

    uv run python video/cut_from_take.py --media ~/projects/sf3d-ai-lab/media/silent-context --take takes/demo
    uv run python video/cut_from_take.py --media ... --take takes-v3/demo --narration video/narration-v3.md --scenes-json audio/scenes-v3.json --prefix v3-

Reads <media>/<take>.events.json (the "block NN" marks record.py wrote) and <media>/<scenes-json> (align.py).
Each narration block becomes one clip, named after the block, cut from the take at its mark and no longer than
its speech plus a tail, so the video is as long as the narration and not as long as the hold. The sentence counts
for the final plan come from the alignment. Rerun after a new take or a new voice.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

TAIL = 1.2  # seconds of picture after the last word
BAND = 130  # pixels of black under the picture for the captions; with a 1920x950 picture the video is 1920x1080


def names_of(narration: Path) -> dict[str, str]:
    """Block number to a clip name from the block's header: '## 05 · Use · 15 s · 40 words' gives '05-use'."""
    text = narration.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^## (\d\d) · ([^·\n]+) · \d+ s · \d+ words$", text, re.M):
        slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).strip().lower()).strip("-")
        out[m.group(1)] = f"{m.group(1)}-{slug}"
    if not out:
        raise SystemExit(f"{narration}: no '## NN · name · S s · W words' blocks")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--media", required=True, help="the video's folder under media/")
    ap.add_argument("--take", default="takes/demo", help="the take, relative to --media, without .mp4")
    ap.add_argument("--scenes-json", default="audio/scenes.json", help="align.py's output, relative to --media")
    ap.add_argument("--narration", default=Path(__file__).with_name("narration.md"), help="the narration, for the clips' names")
    ap.add_argument("--name", default="silent-context-en", help="the final's name in the plan")
    ap.add_argument("--prefix", default="", help="a prefix for the written files: 'v3-' gives v3-cut.json and v3-final.json")
    ap.add_argument("--out", default=Path(__file__).parent, help="where the cut list and the final plan go")
    ap.add_argument("--band", type=int, default=BAND, help="the captions' band under the picture in pixels; 0 for the "
                    "9:16 social cut, whose captions sit in the platforms' safe area over the picture")
    a = ap.parse_args()
    media = Path(a.media).expanduser()
    names = names_of(Path(a.narration))
    events = json.loads((media / f"{a.take}.events.json").read_text(encoding="utf-8"))
    marks = {e["label"]: e["at_s"] for e in events["events"]}
    aligned = json.loads((media / a.scenes_json).read_text(encoding="utf-8"))
    speech = {s["scene"]: s["end"] - s["start"] for s in aligned["scenes"]}
    sentences = Counter(s["scene"] for s in aligned["sentences"])
    blocks = sorted(names)
    missing = [b for b in blocks if f"block {b}" not in marks or b not in speech]
    if missing:
        raise SystemExit(f"no mark or no speech for blocks {missing}")
    scenes = []
    for i, block in enumerate(blocks):
        start = marks[f"block {block}"]
        hold_end = marks[f"block {blocks[i + 1]}"] if i + 1 < len(blocks) else marks["done"]
        end = min(hold_end, start + speech[block] + 0.3 + TAIL)
        scenes.append({"name": names[block], "parts": [{"take": a.take, "from": round(start, 2), "to": round(end, 2)}]})
    cut = {
        "about": "Silent context: one clip per narration block, cut from the one take by its block marks, each no longer than its speech plus a tail (cut_from_take.py). Nothing is sped up. Paths are relative to --media.",
        "size": events["size"],
        "speed_of_waits": 1,
        "scenes": scenes,
    }
    final = {
        "about": "Silent context: the final plan (pipeline/final.py), written by cut_from_take.py from the alignment. Each narration block is one clip; its sentences start 0.3 s into the clip, which already shows what they talk about. The captions are burned into a black band under the picture, never over it. The guide run uses the same plan with --narration, --scenes-json and --name; the owner's own track replaces audio/narration.wav last.",
        "name": a.name,
        "size": events["size"],
        "band": a.band,
        "narration": "audio/narration.wav",
        "scenes_json": a.scenes_json,
        "scenes": {block: {"clip": names[block], "blocks": [[0, sentences[block] - 1, 0.3]]} for block in blocks},
    }
    out = Path(a.out)
    (out / f"{a.prefix}cut.json").write_text(json.dumps(cut, indent=1) + "\n", encoding="utf-8")
    (out / f"{a.prefix}final.json").write_text(json.dumps(final, indent=1) + "\n", encoding="utf-8")
    total = sum(s["parts"][0]["to"] - s["parts"][0]["from"] for s in scenes)
    print(f"{len(scenes)} clips, {total:.1f} s of picture, from {a.take} -> {a.prefix}cut.json, {a.prefix}final.json")


if __name__ == "__main__":
    main()

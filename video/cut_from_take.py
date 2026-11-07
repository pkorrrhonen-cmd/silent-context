"""Write cut.json and final.json from a take's marks and the aligned narration.

    uv run python video/cut_from_take.py --media ~/projects/sf3d-ai-lab/media/silent-context --take takes/demo

Reads <media>/<take>.events.json (the "block NN" marks record.py wrote) and <media>/audio/scenes.json
(align.py). Each narration scene becomes one clip, cut from the take at its mark and no longer than its
speech plus a tail, so the video is as long as the narration and not as long as the hold. The sentence
counts for final.json come from the alignment. Rerun after a new take or a new voice.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

NAMES = {
    "01": "whole", "02": "gap", "03": "capture", "04": "bind", "05": "use", "06": "learn",
    "07": "ageing", "08": "not-for-all", "09": "disagree", "10": "barrier", "11": "limits",
}
TAIL = 1.2  # seconds of picture after the last word


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--media", required=True, help="the video's folder under media/")
    ap.add_argument("--take", default="takes/demo", help="the take, relative to --media, without .mp4")
    ap.add_argument("--scenes-json", default="audio/scenes.json", help="align.py's output, relative to --media")
    ap.add_argument("--out", default=Path(__file__).parent, help="where cut.json and final.json go")
    a = ap.parse_args()
    media = Path(a.media).expanduser()
    events = json.loads((media / f"{a.take}.events.json").read_text(encoding="utf-8"))
    marks = {e["label"]: e["at_s"] for e in events["events"]}
    aligned = json.loads((media / a.scenes_json).read_text(encoding="utf-8"))
    speech = {s["scene"]: s["end"] - s["start"] for s in aligned["scenes"]}
    sentences = Counter(s["scene"] for s in aligned["sentences"])
    blocks = sorted(NAMES)
    scenes = []
    for i, block in enumerate(blocks):
        start = marks[f"block {block}"]
        hold_end = marks[f"block {blocks[i + 1]}"] if i + 1 < len(blocks) else marks["done"]
        end = min(hold_end, start + speech[block] + 0.3 + TAIL)
        scenes.append({"name": f"{block}-{NAMES[block]}", "parts": [{"take": a.take, "from": round(start, 2), "to": round(end, 2)}]})
    cut = {
        "about": "Silent context: eleven clips cut from the one take by its block marks, each no longer than its speech plus a tail (cut_from_take.py). Nothing is sped up. Paths are relative to --media.",
        "size": events["size"],
        "speed_of_waits": 1,
        "scenes": scenes,
    }
    final = {
        "about": "Silent context: the final plan (pipeline/final.py), written by cut_from_take.py from the alignment. Each narration scene is one clip; its sentences start 0.3 s into the clip, which already shows what they talk about. The guide run uses the same plan with --narration, --scenes-json and --name; the owner's own track replaces audio/narration.wav last.",
        "name": "silent-context-en",
        "size": events["size"],
        "narration": "audio/narration.wav",
        "scenes_json": a.scenes_json,
        "scenes": {block: {"clip": f"{block}-{NAMES[block]}", "blocks": [[0, sentences[block] - 1, 0.3]]} for block in blocks},
    }
    out = Path(a.out)
    (out / "cut.json").write_text(json.dumps(cut, indent=1) + "\n", encoding="utf-8")
    (out / "final.json").write_text(json.dumps(final, indent=1) + "\n", encoding="utf-8")
    total = sum(s["parts"][0]["to"] - s["parts"][0]["from"] for s in scenes)
    print(f"{len(scenes)} clips, {total:.1f} s of picture, from {a.take}")


if __name__ == "__main__":
    main()

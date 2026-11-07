# Silent context: the video's narration, v3

**State:** v3, 7.11.2026 evening, the second cut (decision 18, the owner chose A). The sentences are the ones in
`narration-read-v3.txt`, which the owner voices in ElevenLabs; twelve blocks, one per picture, in the aligner's form
(`VIDEO-RULEBOOK.md` §3, whole seconds). The final video of 7.11. on v2 (`narration.md`) stays the fallback.

**Why a v3.** Read as a judge and as an ordinary viewer, v2 is correct but dense: a new concept every ten
seconds, the page at video size too small to read, and the words claim, bound and scope are ours, not the
viewer's. v3 tells one story in plain words, shows the page zoomed on the one panel the sentence is about, and
keeps the harder cases short. No word the viewer has to learn first: a claim is a note, binding is pinning, the
scope is which units it covers, a class is a model.

**The picture** (`scenes_v3.py`): the cards are `story.html`, in the page's look, with a still state at the end of
every move; the page is zoomed by a transform on its body that the recorder injects, so the product's page is
not changed. Measured 7.11.: with `will-change` on the body the screencast gave 4 frames in a 0.6 s move;
without it, a frame every 17 ms (73 frames in a 1.2 s move), so the move is smooth and the text stays crisp.

Total: 305 words over 114 s, about 2.7 words a second.

Pronunciation: TRN as the letters "T R N"; Erkki "ERK-ki"; Veikko "VAY-ko"; Elisa "EH-lee-sa".

| Block | Picture |
|---|---|
| 01 The story | story.html card 0: the chat types itself, then "It lives in one chat." |
| 02 The answer | story.html card 1: four steps light up in turn |
| 03 Capture | page scene 2, zoom on What was read |
| 04 Pin | page scene 3, zoom on the note, then on the graph |
| 05 Use | page scene 4, zoom on the agent's answer |
| 06 Learn | page scene 5, zoom on From the devices |
| 07 Doubt | page scene 6, zoom on the answer |
| 08 Not for all | page scene 7, zoom on the answer |
| 09 Disagree | page scene 8, zoom on the answer |
| 10 The barrier | page scene 9, zoom on the access answer |
| 11 The limits | story.html card 2: four lines appear one by one |
| 12 Close | story.html card 3: the name, the repository, no model and no key |

---
## 01 · The story · 14 s · 37 words

Veikko changed a part on a network unit. The link came up, but no traffic. Erkki knew the fix: disable the port, wait, enable it again. Is it written down anywhere? No. It lives in one chat.

## 02 · The answer · 13 s · 35 words

Silent context reads that chat as it is, pins the advice to the unit it was about, and remembers who said it and when. The next time, an agent gets the answer in one call.

## 03 · Capture · 8 s · 22 words

The thread and an email are read exactly as written. Nobody fills in anything. The system never starts a conversation with anyone.

## 04 · Pin · 14 s · 37 words

Erkki's advice becomes one note, in his own words, pinned to the unit TRN-042. It keeps who said it, where, and which units he said it covers. It is dated from the moment the part was changed.

## 05 · Use · 15 s · 40 words

A week later, the same fault on another unit of the same model. The agent reads the counters from the device itself and proposes Erkki's step, with its source. A reboot stays held back until the lighter fix has failed.

## 06 · Learn · 8 s · 22 words

What the technician did, and that it worked, comes from the device's own events. The note fills itself in. Nobody reported anything.

## 07 · Doubt · 8 s · 21 words

It also knows when not to trust itself. After a firmware update, it asks to check again on that unit only.

## 08 · Not for all · 4 s · 10 words

Where the fix did not help, it stops offering it.

## 09 · Disagree · 4 s · 11 words

When two experts disagree, it shows both and picks no side.

## 10 · The barrier · 7 s · 20 words

And before anyone drives to a site: where the key is now, who said so, and how old that is.

## 11 · The limits · 14 s · 37 words

What this does not claim. It never starts a conversation with an expert. It shows where advice came from, not whether it is true. It scores advice, never people. Everything but Elisa's two example files is simulated.

## 12 · Close · 5 s · 13 words

Silent context. Runs with no model and no key. The code is public.

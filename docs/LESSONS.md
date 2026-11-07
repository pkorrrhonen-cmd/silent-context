# Since AI 2026 LESSONS

Newest first. The **root cause** is the heading, not the symptom, because the root cause repeats
elsewhere. Only lessons whose price was actually paid. A lesson that becomes a permanent rule moves
into `CLAUDE.md`.

## A new unit at a site that already has one makes every mention of that site ambiguous

On 7.11.2026 evening the fourth unit, TRN-063, was first placed at Rauta beside TRN-051. Two resolver tests
and one held-out row changed at once: a thread that names only the site had bound to the one unit there, and
now waited with "several could fit". The binding rule was right; the data had changed what a site name
means. The unit was moved to a site of its own, and the numbers came back.

**Rule:** before adding an entity to the graph, list the mentions that resolve through its neighbours,
and expect those bindings to change; a held-out number that moves after a graph change is a data change,
not a rule change.

## A clip cut at a mark opens on the frame the screencast had before the mark

On 7.11.2026 the owner saw a one-frame flash at 1:55 of the second cut: the opening story card, between the
barrier scene and the limits card. The story page loads with its first card shown; the recorder switched to
the limits card and marked the block in the same instant, and the screencast's frame at that instant was the
one painted before the switch. Every clip is cut from its mark, so the clip's first frame was the wrong card.
The page's scenes never showed this, because the recorder waited 0.6 s after each scene before marking.

**Rule:** before a mark, the picture the clip must open on has been painted and captured: show nothing until
the block, switch, wait two animation frames, then mark.

## `will-change: transform` moves a page on the compositor without a paint, so a screencast sees no frames

On 7.11.2026 the first zoom trial put `will-change: transform` on the page's body, as a performance habit,
and a 0.6 s zoom came through the screencast as 4 frames: the compositor animated the layer without the
page painting, and the screencast delivers a frame only when the page paints. Without the property the
same move gave a frame every 17 ms.

**Rule:** no `will-change` on anything a screencast must follow; measure the frames of a move before
building on it.

## A screencast delivers frames only when the page paints, so a fade's last frame can be lost

On 7.11.2026 the pitch cards in front of the video faded in over half a second, and in the first take
the first card stayed dim for its whole hold: the screencast had sent a mid-fade frame and dropped the
final one, because it delivers a frame only after the previous one is acknowledged and the card painted
nothing after the fade. The page's scenes never showed this, because the page keeps painting (the
clock, the transitions). The take was recorded again with a hard cut.

**Rule:** a card or still that is recorded as a screencast changes in one paint, with no animation; or
the frame is checked at the end of the hold, not at its start.

## One run of a model is one sample, not a measurement

On 6.11.2026 the first scored run gave 0 of 16 confidently wrong on the held-out set, and that number
went into the changelog and to the owner as the result. Later runs gave 1 of 16, and five clean repeats
gave 0, 0, 0, 1, 1, the same file each time. The first number was true of that run and said little about
the system. The temptation after a bad run is to run again until the number looks right, and that only
makes the mistake harder to see.

**Rule:** before quoting a number from a model, repeat it with the prompt unchanged and report the range.
Keep the newest recording, not the best one.

## A review run in the same command as the commit cannot stop the commit

On 6.11.2026 the staged list was printed and the commit ran in one shell command. The list showed
`data/truth/` as untracked, but the commit had already gone through by the time it could be read, so
`b523c43` claims a truth set it does not contain. History is not rewritten here, so the fix is a
second commit and a wrong message that stays.

**Rule:** read `git status` and `git diff --staged` in one step and commit in the next.

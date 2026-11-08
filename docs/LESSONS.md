# Since AI 2026 LESSONS

Newest first. The **root cause** is the heading, not the symptom, because the root cause repeats
elsewhere. Only lessons whose price was actually paid. A lesson that becomes a permanent rule moves
into `CLAUDE.md`.


## A demo that tells the story is judged beside products that take a question, and usability was the first criterion

Third of fifteen in Elisa's challenge (8.11.2026). The two entries ahead ran live: a Slack bot that captured while
the judge watched and an app that opens with "What are you stuck on?", both with real models and held-out evals shown
inside the product. Silent context ran with no model and no key on purpose, as a page of thirteen scenes with
recorded answers; the honesty and the documents were as good or better, but a judge could not ask it anything. The
brief also allowed one-click questions to the specialist, and both winners used them; decision P6 read the brief
more strictly than it asked. Both winners talked to Elisa at the venue during the event and cite it.
[`retrospective.md`](retrospective.md) has the comparison.

**The rule:** at a hackathon, build the live path a judge can type into first and keep the keyless path as the
second one; read the brief for what it allows; put the evals in the product; and talk to the challenge owner on the
first evening.

## A generated plan carries a default input, and a finisher that caches its work hides a wrong one

On 8.11.2026 evening the result cut of the vertical video was delivered with the wrong voice: the final plan that
`cut_from_take.py` writes names the submission video's track by default, `final.py` was run without `--narration`,
and the check before delivery looked at frames of the picture, never at the sound. The owner heard it at once. The
first rerun with the plan corrected changed nothing, because `final.py` keeps the normalised track and the encoded
scenes under `final/work/<name>` and reuses them unless `--force` is given; the unchanged file sizes were the clue.

**The rule:** before a video is delivered, its sound is checked as its picture is: the final's own audio aligned to
the words, or correlated against the track it should carry. A generated plan is read before it is run, and every
input it names is the one meant; a tool that caches is rerun with its force flag after any input changes.

## A ready pipeline and approved words tempt a build before the storyboard, and the owner's planning step is skipped

On 7.11.2026 evening the owner asked for a 30 second vertical video of the submitted work for his own channels.
The pipeline, the look and the narration's words were all ready, so the session wrote six cards from the
submission's story and built a guide cut in one go. The owner's reply: this went minimally wrong, we did not hold
the planning phase; the video matters to his family, colleagues and work contacts, its audience knows nothing of
the subject, and the picture had to be made for a portrait screen from the start. The storyboard was then agreed
scene by scene and the video rebuilt; the first cut cost about an hour.

**Rule:** a video for a new audience is a new video, however ready the material: storyboard and narration v0
first, the owner's sign-off, then the build (the video rulebook's steps), also for a "short version" of an
approved video.

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

## Nothing else runs while a take records

On 7.11.2026 the v6 take was recorded while a deck build, a LibreOffice export and a page render ran on the
same machine. The owner saw two jerks in the zoom at 0:56 and 1:10. The take's frame list showed why: one
frame of 0.43 s and two of 0.27 and 0.30 s inside the first two zoom moves, in the minute those jobs ran,
and none later; the v5 and v4 takes, recorded on a quiet machine, had no frame over 50 ms in any move.
The screencast only delivers what the browser paints, and a busy CPU paints late.

**Rule:** a take is recorded alone: nothing else is started until it is done, and the frame list is read
for stalls before the cut.

## A look decided last costs a take, a deck and an evening

On 7.11.2026 the page, the cards and both decks were built with no decision about colours or a look: the
first dark palette stayed because nothing replaced it, and after package V4 the owner saw the whole as very
dark. The content was done and the voice was aligned, so the change was one token block and a new take,
about two hours; but every picture, crop, deck and the README's image had to be made again, and the video
was recorded a sixth time for the same words. The look is a decision like any other, and it was never on the
list.

**Rule:** before the first page is built, decide the palette and the heading font in one token block, from
the audience's screen (a phone in a bright hall here) and the challenge owner's own look; a change later
should be a change to that block and nothing else.

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

# Since AI 2026 LESSONS

Newest first. The **root cause** is the heading, not the symptom, because the root cause repeats
elsewhere. Only lessons whose price was actually paid. A lesson that becomes a permanent rule moves
into `CLAUDE.md`.

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

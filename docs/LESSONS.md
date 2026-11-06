# Since AI 2026 LESSONS

Newest first. The **root cause** is the heading, not the symptom, because the root cause repeats
elsewhere. Only lessons whose price was actually paid. A lesson that becomes a permanent rule moves
into `CLAUDE.md`.

## A review run in the same command as the commit cannot stop the commit

On 6.11.2026 the staged list was printed and the commit ran in one shell command. The list showed
`data/truth/` as untracked, but the commit had already gone through by the time it could be read, so
`b523c43` claims a truth set it does not contain. History is not rewritten here, so the fix is a
second commit and a wrong message that stays.

**Rule:** read `git status` and `git diff --staged` in one step and commit in the next.

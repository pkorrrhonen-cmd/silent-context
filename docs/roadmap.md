# Since AI 2026: roadmap

Order and gates only. The tasks are in [`BACKLOG.md`](BACKLOG.md) (the only task list), the state in
[`BUILD_INFO.json`](BUILD_INFO.json), the done work in [`CHANGELOG.md`](CHANGELOG.md). Updated
**7.11.2026**. A gate is falsifying: it says what blocks, never "approved".

## Where we are

Elisa's challenge is selected and the design decisions are made
([`DECISIONS.md`](DECISIONS.md)). The build follows the phases in the Atlas artifact
`SINCEAI-2026-ELISA-RAKENNUSSUUNNITELMA`. Phases 0 to 6 are done, and phase 6's checkpoint with the owner
is open.

## The build's order

| Phase | What | Checkpoint with the owner |
|---|---|---|
| 0 | Skeleton and health check | |
| 1 | Synthetic data and truth set, before any rule | Yes |
| 2 | Store and seed graph | |
| 3 | Extraction and binding | Yes |
| 4 | `claims_for` and the agent | Yes |
| 5 | Events, ageing, conflict | |
| 6 | Web page and graph | Yes |
| 7 | Acceptance runs and a clean install | |
| 8 | Video, slides, documentation | |
| 9 | Submission, by Sunday 09:30 | |

## The event's schedule

Source: sinceai.ai/hackathon, read 4.11.2026 (Atlas `SINCEAI-2026-PYSTYTYS-HANDOFF`). Times are
Finnish time.

| When | What |
|---|---|
| Thu 5.11. 15:00 | Challenge summaries open in sinceai.app |
| Fri 6.11. 15:00 | Check-in |
| Fri 6.11. 16:45 | Team formation closes |
| Fri 6.11. 17:00 | Opening |
| Fri 6.11. 17:30 | **Challenge selection closes, final** |
| Sun 8.11. 10:00 | **Submissions close** in sinceai.app |
| Sun 8.11. 12:00 | Participant vote closes |
| Sun 8.11. 13:15 | Closing |
| Sun 8.11. 14:00 | Finals, ending around 15:30 |

## Gates

**Before the submission:** blocked if the README does not name the challenge, the demo and how to
run it; if "Pre-existing work" or "AI tools used" no longer tells the truth; if the submission link
does not open for the jury; or if a team member has not accepted the IP terms in sinceai.app.

**Before any flip to public:** blocked until gitleaks has run over the full history
([`BACKLOG.md`](BACKLOG.md) REPO-3).

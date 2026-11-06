# Since AI 2026: decisions (decision boxes)

The list the boxes are asked from: one numbered row per decision, asked four at a time, the answer
recorded here before the next batch. **This file is the truth, the conversation is not.** States:
`draft` (not asked yet), `OK` (decided as recommended), `edit` (decided otherwise; the row says how),
`drop`, `later` (deferred; the row says until when).

Decided before this list and not re-opened here: the decisions of 4.11.2026 in the Atlas artifact
`SINCEAI-2026-SUUNNITELMA`.

Updated 6.11.2026 (session 2).

| # | Where | What now | State |
|---|---|---|---|
| 1 | The challenge | Elisa, selected 6.11.2026. Final. | `OK` |
| 2 | Visibility | Private. The IP terms are read. The submission form asks for a repository link, so this is decided before the submission; gitleaks over the full history before any flip to public. | `later`, before the submission on 8.11. |
| 3 | License | None chosen. The terms: the team owns what it builds, and Elisa can use it in its business. | `later`, before the submission on 8.11. |

## Design decisions P1 to P6

Made by the owner on 6.11.2026 after six confirmation rooms. Their reasoning, the rooms' results and
what each means as a build are in the Atlas artifact `SINCEAI-2026-ELISA-PAATOKSET`; the identifiers
are its decision log rows. The room confirmed P1, P3 and P6. It differed on P2, P4 and P5, and the
owner decided those again on the room's reasoning.

| # | Where | Decided | Decision log |
|---|---|---|---|
| P1 | Claim store | SQLite tables, a graph view drawn separately, a graph export (JSON at least). | `dec_20d53011c12642b2` |
| P2 | Claim model and binding | Claim text, plus the observed entity, plus a separate scope with verbatim wording and a status, plus minimum relations. Optional procedure fields only if time remains. | `dec_fd91ea0039e64503` |
| P3 | Validity and ageing | World time and information time apart. One fixed recheck rule, computed at read time per claim and unit. No per-type expiry windows. | `dec_07488a1220a44310` |
| P4 | Evidence | Evidence events with a date and a link, rendered from a template. No ratios, percentages, independence counts or per-person figures. | `dec_f5ea70626b7446f9` |
| P5 | Sources in the demo | Teams and email exports, plus a synthetic event stream as the time anchor and the outcome check. A scripted transcript only on three conditions. No real call. | `dec_21d178d95bf24528` |
| P6 | A human in the capture loop | Never: the system does not start a conversation with a specialist. An unclear binding waits with its reason. | `dec_ad4eb290613c4e27` |

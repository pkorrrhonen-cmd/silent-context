# Since AI 2026: decisions (decision boxes)

The list the boxes are asked from: one numbered row per decision, asked four at a time, the answer
recorded here before the next batch. **This file is the truth, the conversation is not.** States:
`draft` (not asked yet), `OK` (decided as recommended), `edit` (decided otherwise; the row says how),
`drop`, `later` (deferred; the row says until when).

Decided before this list and not re-opened here: the decisions of 4.11.2026 in the Atlas artifact
`SINCEAI-2026-SUUNNITELMA`.

Updated 7.11.2026 (session 3).

| # | Where | What now | State |
|---|---|---|---|
| 1 | The challenge | Elisa, selected 6.11.2026. Final. | `OK` |
| 2 | Visibility | Public as soon as the product is in a shape the repository can be opened in, before the submission. gitleaks is installed and run over the full history, and `CLAUDE.md` and `docs/` are read for anything internal, at that point. The owner, 7.11.2026. | `OK` |
| 3 | License | None chosen. The terms: the team owns what it builds, and Elisa can use it in its business. Chosen when the repository goes public; MIT recommended, because the jury and Elisa can then use it without a question. | `later`, before the flip to public |
| 4 | Truth set, the second expert's claim | Corrected: the claim waits with `no_id`. The truth set first bound it to TRN-051, and the model left it waiting, because the advice is about old units in general and TRN-051 only prompted it. The file says this was done after the first scored run, which makes that row weaker evidence than the rest. | `OK` |
| 5 | Measuring run-to-run variation | Done: five repeats with the prompt unchanged and no rule tuned to them. Confidently wrong per run, of 16: 0, 0, 0, 1, 1, the same one file each time. See `data/truth/held_out_repeats.json`. | `OK` |
| 6 | IP terms | Accepted in sinceai.app when the challenge was selected. The owner, 7.11.2026. | `OK` |
| 7 | Product name | Silent context, the working name made final. The repository was renamed `silent-context` on 7.11.2026, and GitHub redirects the old name. The owner, 7.11.2026. | `OK` |
| 8 | Phase 6 checkpoint: the page | Changes: at first glance the page looks confusing. Session 3 makes it clearer wherever it can, and the owner looks again. The owner, 7.11.2026. | `edit` |
| 9 | Cypher export and a Neo4j trial run | Done in session 3, because the build is ahead of the plan and the owner wants it. The owner, 7.11.2026. | `OK` |
| 10 | The video's shape | The whole idea is clear in the first 20 seconds. After that, how it happens is shown as a short, clear presentation. At about 60 seconds the viewer has fully grasped what this is. The owner, 7.11.2026. | `OK` |
| 11 | Something useful or distinguishing with the spare time | The MCP wrapper: the agent's calls as MCP tools, so an agent that speaks MCP asks the store directly. Needs the `mcp` package, added. The owner, 7.11.2026. | `OK` |
| 12 | The video's picture | Approved as a pre-version in the larger-text take. The captions go into a black band of their own under the picture, never over it, because the frame holds many views and text. The owner, 7.11.2026. | `OK` |
| 13 | A pitch in front of the video | About 20 seconds, very concise: what the problem is, how it is solved; then the video shows it in practice. Elisa's representative must first grasp what the solution does, then see it as a technical solution. Built as two cards in the page's look (`video/pitch.html`), narration blocks 01 and 02, replacing the earlier overview block over the page. The owner, 7.11.2026; the words and the cards wait for his reaction. | `edit` |
| 14 | The final voice | The owner produces the track in ElevenLabs and hands it over here; the session aligns it to the picture with the same plan. The owner, 7.11.2026. | `OK` |

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

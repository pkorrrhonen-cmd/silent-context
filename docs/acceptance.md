# Acceptance cases

Written by `uv run python -m app.accept` on 2026-11-07 from the recorded answers, with no model and no key. The cases are the build plan's A1 to A11, with A0 for the question before anything is captured. The stores are built at each case's clock from `data/`, as the tests do; the checks are the ones in `tests/test_claims.py`. A9 reports numbers and is not a pass or a fail: they describe this set of 16 synthetic sources only. A10 was done by hand and is quoted from the changelog.

Computed rows holding: 21 of 21.

| Case | Asked | Expected | Observed | Result |
|---|---|---|---|---|
| A0 | TRN-051, the symptom, before anything is captured (14.10. 22:00) | I don't know, reason no claims, ask transmission-oncall | unknown, reason no_claims, ask transmission-oncall | ok |
| A1 | TRN-051, the symptom, counters not reported (20.10.) | check first, same class, read the counters, reboot and replacement held back, reach called an inference | check_first, same_class, read, held back, called an inference | ok |
| A1 | TRN-051, counters reported zero (20.10.) | propose the bounce, same class, held back; the claim's scope undefined, Teams and email as one telling | propose, same_class, bounce_interface, held back; scope undefined, sources email and teams | ok |
| A1 | TRN-051 during the fault, nothing reported (21.10. 10:50) | the agent reads zero counters from telemetry itself and proposes | counters zero from telemetry; propose | ok |
| A2 | TRN-100, a newer unit, before anyone narrows the advice (20.10.) | named a guess, check first, read; never a proposal | similar_guess, check_first, read; "A guess:..." | ok |
| A2 | TRN-100 after the failure and the narrowing (31.10.) | not proposed, not the bounce; the advice shown as not applicable with the reported failure | check_first, read; the advice not_applicable, match none, narrowed to 4.x firmware, failure on TRN-100 shown | ok |
| A2 | TRN-051 after the narrowing (31.10.) | still proposed, same class, now a confirmed scope | propose, same_class, scope confirmed as 4.x firmware | ok |
| A3 | TRN-051, a different symptom (20.10.) | I don't know, no claims, ask transmission-oncall, the gap logged | unknown, reason no_claims, ask transmission-oncall, no claims, gap logged for transmission-oncall | ok |
| A4 | Access to Nilo before the key moved (20.10.) | the grey box, with the information age in days | propose, the grey box, information age 47 days | ok |
| A4 | Access to Nilo after the move (21.10.) | the maintenance hut; the old location superseded with its end date | the maintenance hut; boundary known; active and superseded; the old one valid_to 2026-10-19 | ok |
| A4 | Access to Nilo at a point in world time, 10.10. | the grey box, the hut not shown | the grey box; boundary known; the hut not in the evidence | ok |
| A4 | The same move with no date in the email | both may hold, the boundary not known, the old end marked unknown | boundary not known; 2 may hold; now the hut, the old end superseded_end_unknown | ok |
| A5 | After a firmware update on TRN-042 only (29.10.) | TRN-042: check first, recheck, the versions named; TRN-051: proposed, active | TRN-042: check_first, recheck, 4.8 to 4.9 named; TRN-051: propose, active | ok |
| A6 | Teams and email from the same teller | one Told line; no two, twice, several, independent or percent in any rendered evidence | 1 Told line, Teams and email on it; no count word at three clocks: none | ok |
| A7 | Two experts disagree (3.11.) | check first, read the counters, the agent does not choose; both shown, the waiting one not offered | check_first, read, does not choose; the first disputed, the second disputed and not offered | ok |
| A8 | The prohibition with nothing reported | no reboot or replacement, held back | read, held back | ok |
| A8 | The prohibition after a bounce with no result | read, still held back | read, held back | ok |
| A8 | The prohibition after a failed bounce | a reboot may be proposed, nothing held back | propose, reboot, no prohibition | ok |
| A9 | The held-out binding set, 16 synthetic sources | unclear cases wait with a reason, controls bind; the wrong ones counted, not tuned | of 16: waited right 11, bound right 4, over-cautious 0, confidently wrong 1, errors 0; five repeats, wrong per run: 0 0 0 1 1 | measured |
| A10 | A clean install from the README into an empty folder, with no key | the seeded store, the agent and the graph work; ingest reads the recorded answers and says it needs a model only for a changed prompt | Passed on 7.11.2026 from `git archive` into an empty folder: 150 tests, seed, ingest, truth report, the agent, both exports (CHANGELOG, session 3) | by hand |
| A11 | The extra-work panel (15.10.) | conversations started 0, actions asked 0, Elisa's files shown unchanged by checksum | conversations started 0, actions asked 0, Elisa's 2 files shown unchanged by checksum: yes | ok |
| A12 | Who acts: TRN-051 on 21.10., then TRN-063 on 25.10. after the first was carried out | a person the first time; the agent once its own log shows the step carried out on this class with the counters rising, and the agent's own bounce recorded as its own from the devices | TRN-051 21.10.: propose, person; TRN-063 25.10.: propose, agent; done by agent, Counters rising afterwards | ok |

# Synthetic data: what was generated and how

Elisa's example material is deliberately small: one case, told in one conversation and one email.
Elisa's ground rules allow generating more in the same style, including other devices, advice that
goes out of date and conflicting advice, as long as it is documented. This is that documentation.

## What is Elisa's and what is invented

| Path | What | Origin |
|---|---|---|
| `data/sources/teams_trn042.json` | The Teams conversation, unchanged (Elisa's `teams_chat.json`) | Elisa |
| `data/sources/email_trn042.txt` | The email, unchanged (Elisa's `email.txt`) | Elisa |
| `data/sources/teams_trn051.json` | A second engineer meets the same fault on another old unit; the advice works | Invented |
| `data/sources/teams_trn100.json` | The advice fails on a newer unit, the expert narrows it to 4.x firmware, and the cause was something else | Invented |
| `data/sources/teams_conflict.json` | A second expert disagrees: replace the SFP first | Invented |
| `data/sources/email_key_nilo.txt`, `email_key_moved.txt` | Where the barrier key is, then a later move | Invented, after Elisa's locked barrier example |
| `data/sources/variants/email_key_moved_undated.txt` | The same move with no date, for one test | Invented |
| `data/sources/teams_noise_*.json` | Lunch, a schedule, a battery check, a handover: no advice | Invented |
| `data/seed/entities.json` | Nodes, classes, sites, the barrier, the procedure type and groups | Invented, apart from the name TRN-042 |
| `data/events/` | Event stream and counter series | Invented, shaped to fit Elisa's conversation |
| `data/truth/expected_claims.json` | The expected result for every source | Written for this demo |
| `data/truth/decoys/`, `expected_decoys.json` | A held-out test set for binding | Written for this demo |

`data/sources/manifest.json` records the checksums of Elisa's two files, and a test keeps them equal.
All other names and identifiers are invented. No real person, network or customer is in the data.

Elisa's two files carry no date, so the demo gives them one from outside: `manifest.json` says when
each source reached the system (a nightly export at 23:00), and the event stream says when the module
was replaced. Those dates are invented too. Times are in one local time without an offset.

## How it was generated

Written by hand with Claude Code (Claude Opus 5.5), with no generator script. The conversations copy
the style of Elisa's example. Each was written to test one thing:

| Trap in the data | What it tests |
|---|---|
| The thread on TRN-051 also names TRN-042 | The outcome belongs to the right node |
| On-call relays the expert's advice | A relay is not a new telling |
| The email says the advice worked "in several cases" | The teller's general statement does not become evidence or a count |
| TRN-100's traffic comes back after a VLAN fix | A later recovery is not credited to the advice |
| Counters on TRN-100 rise only after a configuration change | Telemetry confirms recovery, not its cause |
| An earlier module replacement on TRN-042 in August | The time anchor picks the right event |
| "Installed around 2019, I think" | An engineer's estimate does not become an age limit |
| "Yesterday" in a dated and an undated email | Code resolves it only from the message's own date |
| A schedule message names TRN-042 and firmware | A mention of firmware is not a firmware update |

## The truth set came first

`expected_claims.json` was written before any extraction or binding code existed.

The held-out set in `data/truth/decoys/` was written by a separate Claude Code agent, which never saw
the binding rules. The author of the rules has not read those files. It holds unclear cases, where the
right result is to wait with a reason, and decidable controls, so a system that always waits does not
score well. Its numbers describe this set only and say nothing about accuracy on real conversations.

## The demo clock

A source is known once the clock has passed its `received_at`, and an event once it has passed its
time. Different acceptance cases need different states of knowledge, so they run at different clock
values, listed in `expected_claims.json`.

| Date | What happens |
|---|---|
| 11.8. | An earlier, unrelated module replacement on TRN-042 |
| 2.9. | The barrier key email |
| 14.10. | The fault on TRN-042, Elisa's conversation and email |
| 20.10. | The key move email (the move itself was on 19.10.) |
| 21.10. | The same fault on TRN-051; the advice works |
| 28.10. | Firmware update on TRN-042 only |
| 30.10. | The advice fails on TRN-100; the expert narrows the scope |
| 2.11. | The second expert disagrees |

The disagreement comes last on purpose. Earlier it would mark the advice disputed for every old unit,
and the cases that show the advice being proposed and rechecked could not run.

## What this data can and cannot show

It shows that the mechanism works end to end on a case the author controlled. It cannot show that
extraction holds on real conversations, that outcomes can be read reliably from real chat, or that
telling apart which units a claim applies to works before someone narrows it down. That last point
rests entirely on how this data was written.

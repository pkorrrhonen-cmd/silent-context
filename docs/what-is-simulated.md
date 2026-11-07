# What is real, what is simulated, what is future

The demo is honest about which of its parts exist and which are stand-ins. This document is the list.
The README's "What the demo does not claim" and the page's last scene say the same in fewer words.

## Real

| Part | What is real about it |
|---|---|
| Elisa's two files | `data/sources/teams_trn042.json` and `email_trn042.txt` are Elisa's example conversation and email, unchanged. A test holds their checksums. Elisa states that their names, node ids and messages are illustrative and contain no production, customer or personal data. |
| The model reading the text | Claude Opus 5.5 read every source through an OpenAI-compatible endpoint, once per thread, with the prompt in `app/extract.py`. Its answers are recorded in `data/extractions/`, unedited, and the demo replays them. The model is not called at demo time. |
| Binding, dating, merging | Code, not the model, ties a claim to a graph entity, dates it from the event stream, and merges one person's accounts. It runs live on every rebuild of the store. |
| The agent | `claims_for` and `access_for` use no model. The tier comes from rules, the evidence from a template, the wording of a step from what the expert said. Every answer on the page is computed when asked. |
| The time axis | What the page shows at a clock value is the store rebuilt from the sources received by then. Nothing is pre-rendered. |
| The numbers on the page | Conversations started by the system: 0, actions asked of specialists: 0. These are zero by construction: no module except the model client can reach outside, and a test holds that. The held-out numbers come from `data/truth/held_out_repeats.json`, five real runs. |
| The graph export | `export/graph.json` and `export/graph.cypher` are written from the store. The Cypher was loaded into an empty Neo4j 5 database on 7.11.2026 with no edits. |

## Simulated

| Part | What stands in, and why |
|---|---|
| Every other source | Nine Teams threads and emails written for this demo, in the style of Elisa's example, each to test one thing ([`synthetic-data.md`](synthetic-data.md)); on the second day a Teams thread in Finnish and a ticket export, to show that the reader does not care about the channel or the language. No real person, network or customer. |
| The dates | Elisa's files carry no date. `data/sources/manifest.json` gives every source a `received_at`, as if a nightly export at 23:00 had brought it. |
| The event stream and telemetry | `data/events/` is invented and shaped to fit Elisa's conversation: a module replaced, a link up, counters at zero, a bounce, counters rising; a firmware update on one unit; a VLAN change on another. There is no network behind it. |
| The graph | `data/seed/entities.json`: four units, two classes, four sites, a barrier, a procedure type and five groups. TRN-042 is the only name from Elisa's material; its class, firmware, ports and site are invented. The Finnish forms of a site's name are aliases, which a production system would take from the inventory or a lemmatiser. |
| The demo clock | Real operations have one present. The demo moves the clock so that each acceptance case runs at its own state of knowledge, and so that the viewer can see what was known when. |
| The channels | Teams and email exports are read from files. Nothing connects to Teams, a mailbox or a ticketing system. |
| The held-out test | 16 synthetic sources written by a separate agent, which never saw the binding rules. The numbers describe this set and say nothing about accuracy on real conversations. |
| The outcome on the device | Counters rising after a bounce are read from the invented telemetry. The rule that records them is real; the data is not. |

## Not built, on purpose

| Idea | Why it is not here |
|---|---|
| Sending the question to the expert | When the agent does not know, it writes the question for the person on call and shows a budget (decision 21). The sending is not built: a person sends, because the system never starts a conversation with a specialist (decision P6), and synthetic data cannot show that a 20-second call is not extra work. |
| Matching Elisa's own graph | Connecting the export to Elisa's inventory needs Elisa's schema, which is not known here. Matching entities is a separate step on the way to production. |
| A better symptom match | Symptoms are matched by plain words over what a claim says. A miss says "I don't know", and a false match still has to pass the claim's own check before anything is proposed. A deployment would want a semantic match here. |
| Acting on a real network | A policy says who acts (decision 20). The agent acts itself only on the reversible bounce, once its own log shows it carried out on the class with the counters rising; in this demo that action is an event written into the synthetic stream, marked as the agent's. There is no step machine and no write path to any device. |
| A "mark as wrong" button | First in the plan's cutting order. A flagged evidence type exists in the schema for it. |
| A scripted call transcript | Decision P5 allowed one only on three conditions, and the demo did not need it. |

## What this means for a reader

The mechanism works end to end on a case the author controlled. It does not show that extraction holds
on real conversations, that outcomes can be read reliably from real chat, or that telling apart which
units a claim applies to works before someone narrows it down. That last point rests entirely on how
the synthetic data was written.

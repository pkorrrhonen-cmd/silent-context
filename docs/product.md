# Since AI 2026: product

This document says **for whom, what, and what never**. The decisions behind it are in
[`DECISIONS.md`](DECISIONS.md).

## For whom

Network operations at a telecom operator: field engineers and on-call staff who meet a fault, the
experts who know how to read it, and the agents that are meant to run the autonomous cycle. The
primary measure is that the people who hold the knowledge do nothing extra.

## What

A system that reads the conversations and emails specialists already write, keeps what they know as
context claims bound to network entities, and gives an agent one call, `claims_for`, that answers
with a next step, its sources and how much is known.

- A claim keeps its original wording, including words like "sometimes" and "usually".
- The entity a claim was observed on and the scope it is said to apply to are separate. The scope
  keeps its wording and has a status: confirmed or undefined.
- World time and information time are separate. Unknown time stays unknown.
- Evidence is a list of events (told, reported success, reported failure, disputed, superseded) with
  a date and a link, rendered from a template.
- The agent answers on three tiers: propose, check first, or "I don't know" with the group to ask.

## What never

- **The system never starts a conversation with a specialist.** The promise is exactly this, not
  "no extra work of any kind". An unclear binding waits with its reason, and may wait forever.
- **No person scores.** No personal assessment and no figure shown per person. A teller identifier
  exists per claim, only to merge the same person's accounts, and the agent sees a role and a link.
- **No percentages or counts as confidence.** The agent may not say "several" or "confirmed twice".
- **No action on a real network, and a policy says who acts.** The default is that the agent proposes and a
  person acts. The agent itself acts only on a step that is reversible, that its own log shows was proposed
  on this class before and carried out with a good outcome, with no disagreement on record, and with the
  counters read from the device by the agent. A reboot or a hardware replacement never goes to the agent. In
  this demo the network is synthetic: the agent's action is an event in the synthetic stream, and there is
  no write path to any device (decision 20, 7.11.2026).
- **No invented time or scope.** An age limit is not derived from "installed around 2019".

## The event's rules

Source: sinceai.ai/hackathon, read 4.11.2026 (Atlas `SINCEAI-2026-PYSTYTYS-HANDOFF`).

- AI tools of any kind are permitted; the main tools used are disclosed (the README's "AI tools used").
- Pre-existing work is kept apart from what is built at the event (the README's "Pre-existing work").
- Licences and each challenge's rules and data restrictions apply.

# Since AI 2026: architecture

The prose behind the README's Architecture section. Where this document and a decision in
[`DECISIONS.md`](DECISIONS.md) differ, the decision wins and this is corrected. Written as the build
proceeds: a component is described here when it exists.

## Constraint in force

Every endpoint comes from an environment variable, never from code ([`.env.example`](../.env.example)
lists them). The product runs without the author's environment.

## Components

| Component | State | What |
|---|---|---|
| `data/` | Written | Sources, event stream, seed graph, truth set ([`synthetic-data.md`](synthetic-data.md)) |
| `data/extractions/` | Recorded | The model's answers, keyed by the whole prompt |
| `app/sources.py` | Built | Reads Teams exports and emails as they are |
| `app/llm.py` | Built | Any OpenAI-compatible endpoint, from the environment |
| `app/extract.py` | Built | What the model is asked, and the record of its answers |
| `app/resolve.py` | Built | Binds a claim to an entity from the graph, with no model |
| `app/ingest.py` | Built | Merges, dates and records evidence; the demo clock |
| `app/scoring.py` | Built | Scores a run against the truth set and the held-out set |
| `app/db.py` | Built | The claim store: schema, seed graph, rebuild |
| `app/export.py` | Built | The graph as JSON |
| `app/claims.py` | Built | The agent's calls: `claims_for` and `access_for` |
| `app/ask.py` | Built | Ask the agent from the command line |
| `app/api.py` | `/health`, `/graph`, `/claims_for`, `/access_for` | HTTP interface |

The web page is not built yet.

## What devices add

`app/events.py` works from the event stream and telemetry alone. Nobody is asked anything.

- **Recheck.** A firmware update on a unit puts SFP advice in doubt for that unit only, computed when
  asked and never stored, so it cannot spread to the class. It is nobody's queue and nobody is told. A
  success reported on the unit after the update clears it. If the advice has no known start and arrived
  after the update, the order cannot be told, and the agent says so. This is one fixed rule on purpose:
  replacing a module is the very situation this advice is for, not a reason to doubt it.
- **An outcome seen on the device.** Counters rising soon after a bounce, with no other change in
  between, are recorded apart from anyone's explanation. This confirms recovery, not its cause. Linking
  it to the advice by time and port is a suggestion, so it never counts towards proposing anything.
- **What a person did.** When the agent proposed a bounce, the log later fills in "a person did" and
  "the outcome" from device events. A later decision about autonomy would need that record, and it
  takes nobody's time.

## The agent

`claims_for(unit, symptom)` uses no model, so an answer works without an endpoint and is the same every
time. The tier comes from rules, the evidence from a template, and the wording of a step from what the
expert said, as extracted once.

| Tier | When |
|---|---|
| `propose` | A reported success on this unit's class, no disagreement, and the claim's own check observed to hold |
| `check_first` | Only told so far, the check not yet observed, a guess, a failure reported on this class, or a disagreement |
| `unknown` | Nothing fits, or the advice does not cover this unit: the answer names a group and logs the gap |

- **How a claim reaches a unit:** `same_node`, `same_class`, or `similar_guess`, which is named a guess
  and is never proposed. While a scope is undefined, reaching another unit of the class is called an
  inference in the answer itself.
- **The one prohibition:** no reboot or hardware replacement before a failed bounce is reported. It is
  in code, and it holds even if a claim advises a reboot.
- **What the agent reads itself:** counters nobody reported come from telemetry, if a recent sample
  exists. An old sample is not read as the present.
- **What it never does:** offer a waiting claim as advice for a unit. A waiting claim can still appear
  as the reason for a disagreement, marked as that.

Symptoms are matched by plain words over what a claim says, not by meaning. Both ways of being wrong are
cheap: a miss says "I don't know", and a false match still has to pass the claim's own check before
anything is proposed. A real deployment would want a better match here.

`access_for(place)` answers how to reach a place, with the age of the information. For a point in world
time it says what held then, and if the moment one statement replaced another is unknown, it returns
both and says so.

## The store

SQLite, built from `data/` and never committed: nothing in it is original, so a clean install has a
working store and no binary enters the repository. Agents reach it only through `claims_for`, so the
storage choice can change without touching them.

Some rules from the decisions are held by the schema itself, so a bug cannot quietly break them:

- A world time always has a basis. A claim cannot carry `valid_from` without saying where it came
  from, and an end cannot be both known and unknown.
- A waiting claim has a reason, and a bound claim has an entity that exists in the graph.
- Edge types and evidence types are closed lists.

Two clocks are kept apart. `valid_from` and `valid_to` are world time and may be empty. `received_at`
and `superseded_at` are information time. Status is not stored: it is computed at read time for a
claim and a unit, so an update on one unit cannot spread to its class.

## The graph export

The export is JSON with stable ids, edge types, times and sources, and it maps directly onto a
property graph. It has not been loaded into a graph database. Connecting it to Elisa's own graph needs
Elisa's schema, which is not known here, so matching entities is a separate step on the way to
production. The teller key stays out of the export: it exists only to merge one person's accounts.

## Data flow

1. **Read.** A source becomes a thread of messages, unchanged. Each source read is logged with its
   checksum, also when it held no claim.
2. **Extract.** The model reads the thread and reports what it says, including the known claims it
   repeats, replaces or opposes. The answer is checked against a schema and recorded.
3. **Check against the text.** An identifier or a scope counts only if it is literally in the thread,
   so anything the model made up is dropped here. Excerpts are whole messages, not the model's words.
4. **Bind.** Code resolves what the thread names against the graph. Node, site, port and firmware must
   agree on one entity; otherwise the claim waits with its reason (`no_id`, `multiple_candidates`,
   `unknown_id`, `contradicting_context`). The model never picks an entity.
5. **Date.** A claim's start comes from an event shortly before the conversation, or from a dated
   message; otherwise it stays empty. "Yesterday" is resolved by code from the message's own date.
6. **Merge.** One person's accounts become one claim with several sources and one telling. A relay is
   a source but not a telling. A replacement closes the old claim only for the same thing on the same
   entity; anything else the model calls a replacement is shown as a conflict.

The demo clock decides what is known, so every state of knowledge can be rebuilt.

## Threats

Not assessed yet.

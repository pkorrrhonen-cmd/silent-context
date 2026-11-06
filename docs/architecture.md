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
| `app/api.py` | `/health`, `/graph` | HTTP interface |
| `app/claims.py` | Contract only | `claims_for`: for now it always answers "I don't know" with a reason |

Matching in `claims_for`, the event rules (recheck, telemetry) and the web page are not built yet.

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

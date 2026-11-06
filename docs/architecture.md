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
| `app/db.py` | Built | The claim store: schema, seed graph, rebuild |
| `app/export.py` | Built | The graph as JSON |
| `app/api.py` | `/health`, `/graph` | HTTP interface |
| `app/claims.py` | Contract only | `claims_for`: for now it always answers "I don't know" with a reason |

Extraction and binding, matching, the event rules and the web page are not built yet.

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

Not built yet.

## Threats

Not assessed yet.

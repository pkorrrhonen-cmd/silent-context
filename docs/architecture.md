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
| `app/api.py` | Health check only | HTTP interface |
| `data/` | Written | Sources, event stream, seed graph, truth set ([`synthetic-data.md`](synthetic-data.md)) |

The store (SQLite tables for entities, edges, claims, sources, evidence events, events and the answer
log), extraction and binding, `claims_for` and the web page are not built yet.

## Data flow

Not built yet.

## Threats

Not assessed yet.

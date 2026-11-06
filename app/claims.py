"""The agent's one call: `claims_for`.

For now this fixes the contract and answers "I don't know" with a reason. Nothing can be matched yet,
because extraction does not exist. Matching, status and the other tiers arrive with the agent.
"""

import json
import sqlite3
from datetime import datetime
from uuid import uuid4

from app import db

FALLBACK_GROUP = "transmission-oncall"

WOULD_CHANGE = {
    "no_claims": "A conversation or email about this symptom on this unit or its class.",
    "entity_unclear": "An identifier that names a known unit.",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _unknown(
    conn: sqlite3.Connection, entity_id: str, symptom: str, reason: str, group: str
) -> dict:
    answer_id = f"ans-{uuid4().hex[:12]}"
    next_step = f"Ask {group}."
    asked_at = _now()
    conn.execute(
        "INSERT INTO answer_log (id, asked_at, entity, symptom, tier, next_step, action_kind)"
        " VALUES (?, ?, ?, ?, 'unknown', ?, 'none')",
        (answer_id, asked_at, entity_id, symptom, next_step),
    )
    conn.execute(
        "INSERT INTO gap_log (id, asked_at, entity, symptom, ask_group) VALUES (?, ?, ?, ?, ?)",
        (f"gap-{uuid4().hex[:12]}", asked_at, entity_id, symptom, group),
    )
    return {
        "tier": "unknown",
        "match_level": "none",
        "next_step": next_step,
        "action_kind": "none",
        "prohibition": None,
        "claims": [],
        "evidence_rendered": "",
        "what_would_change": WOULD_CHANGE[reason],
        "ask_group": group,
        "reason_code": reason,
        "answer_id": answer_id,
    }


def claims_for(
    entity_id: str,
    symptom: str,
    at: str | None = None,
    observed: dict | None = None,
    *,
    conn: sqlite3.Connection | None = None,
) -> dict:
    """What is known about this entity and symptom, and what to do next.

    `at` is a point in world time. `observed` is what the user or telemetry reports:
    {"link": "up|down|unknown", "counters": "rising|zero|unknown", "bounce_failed": bool}.
    Neither changes the answer yet.
    """
    if conn is None:
        with db.session() as own:
            return claims_for(entity_id, symptom, at, observed, conn=own)
    row = conn.execute("SELECT attrs FROM entity WHERE id = ?", (entity_id,)).fetchone()
    if row is None:
        return _unknown(conn, entity_id, symptom, "entity_unclear", FALLBACK_GROUP)
    group = json.loads(row["attrs"]).get("responsible_group", FALLBACK_GROUP)
    return _unknown(conn, entity_id, symptom, "no_claims", group)

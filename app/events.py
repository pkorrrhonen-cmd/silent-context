"""What devices add to what people said: a recheck, an outcome, and what a person did.

All of it is computed from the event stream and telemetry. Nobody is asked anything and nobody writes
anything down.
"""

import json
import sqlite3
from datetime import datetime, timedelta

from app.resolve import Graph

# One fixed rule, on purpose. Any change to a unit would be wrong as a trigger: replacing a module is
# the very situation this kind of advice is for, not a reason to doubt it.
RECHECK_PROCEDURES = ("PROC-SFP-REPLACE",)
OUTCOME_WINDOW = timedelta(minutes=10)


def recheck(
    conn: sqlite3.Connection, claim: sqlite3.Row, entity: str, at: str | None = None
) -> tuple[str, str] | None:
    """Whether a firmware update puts this claim in doubt on this unit: a status and its reason.

    Computed when asked, for this claim and this unit, and never stored, so an update on one unit
    cannot spread to its class. It is nobody's queue and nobody is told. A success reported on the unit
    after the update clears it.
    """
    marks = ",".join("?" for _ in RECHECK_PROCEDURES)
    tied = conn.execute(
        f"SELECT 1 FROM edge WHERE src = ? AND rel = 'ABOUT' AND dst IN ({marks})",
        (claim["id"], *RECHECK_PROCEDURES),
    ).fetchone()
    if not tied:
        return None
    update = conn.execute(
        "SELECT event_time, attrs FROM event WHERE entity = ? AND type = 'firmware_updated'"
        " AND (? IS NULL OR event_time <= ?) ORDER BY event_time DESC LIMIT 1",
        (entity, at, at),
    ).fetchone()
    if update is None:
        return None
    settled = conn.execute(
        "SELECT 1 FROM evidence_event WHERE claim_id = ? AND scope_entity = ? AND basis = 'message'"
        " AND type = 'reported_success' AND event_time > ?",
        (claim["id"], entity, update["event_time"]),
    ).fetchone()
    if settled:
        return None

    change = json.loads(update["attrs"])
    when = update["event_time"]
    if claim["valid_from"]:
        if when <= claim["valid_from"]:
            return None
    elif when <= claim["received_at"]:
        return (
            "order_unknown",
            f"The firmware on {entity} changed on {when}, and it is not known whether this advice came"
            " before or after that.",
        )
    return (
        "recheck",
        f"The firmware on {entity} changed from {change.get('from')} to {change.get('to')} on {when},"
        " after this advice, so it needs checking again on this unit.",
    )


def _reaches(graph: Graph, claim: sqlite3.Row, entity: str) -> bool:
    if claim["observed_entity"] == entity:
        return True
    unit_class = graph.nodes.get(entity, {}).get("class_id")
    if claim["scope_status"] == "confirmed":
        return claim["applies_to"] == unit_class
    return graph.nodes.get(claim["observed_entity"] or "", {}).get("class_id") == unit_class


def _first_rise(conn: sqlite3.Connection, up: sqlite3.Row) -> sqlite3.Row | None:
    """The first rise soon after the interface came back, if nothing else changed in between."""
    end = (datetime.fromisoformat(up["event_time"]) + OUTCOME_WINDOW).isoformat()
    rise = conn.execute(
        "SELECT t FROM telemetry WHERE entity = ? AND port = ? AND t >= ? AND t <= ? AND value > 0"
        " ORDER BY t LIMIT 1",
        (up["entity"], up["port"], up["event_time"], end),
    ).fetchone()
    if rise is None:
        return None
    other_change = conn.execute(
        "SELECT 1 FROM event WHERE entity = ? AND type = 'config_changed'"
        " AND event_time >= ? AND event_time <= ?",
        (up["entity"], up["event_time"], rise["t"]),
    ).fetchone()
    return None if other_change else rise


def link_telemetry_outcomes(conn: sqlite3.Connection, graph: Graph) -> None:
    """Counters rising right after a bounce, recorded apart from anyone's explanation.

    This confirms recovery, not its cause. Linking it to the advice by time and port is a suggestion,
    so it does not count towards proposing anything.
    """
    claims = conn.execute(
        "SELECT * FROM claim WHERE action_kind = 'bounce_interface' AND binding_status = 'bound'"
        " AND superseded_at IS NULL"
    ).fetchall()
    ups = conn.execute("SELECT * FROM event WHERE type = 'admin_up' ORDER BY event_time").fetchall()
    for up in ups:
        rise = _first_rise(conn, up)
        if rise is None:
            continue
        for claim in claims:
            start = claim["valid_from"] or claim["received_at"]
            if start > up["event_time"] or not _reaches(graph, claim, up["entity"]):
                continue
            count = conn.execute("SELECT count(*) FROM evidence_event").fetchone()[0]
            conn.execute(
                "INSERT INTO evidence_event (id, claim_id, scope_entity, type, event_time, source_ref,"
                " excerpt, channel, basis) VALUES (?, ?, ?, 'reported_success', ?, ?, ?, 'telemetry',"
                " 'telemetry')",
                (
                    f"evd-{count + 1:03d}",
                    claim["id"],
                    up["entity"],
                    rise["t"],
                    f"telemetry_{up['entity'].lower().replace('-', '')}.json#{up['port']}@{rise['t']}",
                    f"Counters on {up['port']} rose after the interface came back up at"
                    f" {up['event_time']}. This confirms recovery, not its cause; linking it to this"
                    " advice is a suggestion.",
                ),
            )


def settle_answers(conn: sqlite3.Connection) -> None:
    """Fills "the agent proposed, a person did, the outcome" from the devices alone.

    This is the record a later decision about autonomy would need, and it takes nobody's time.
    """
    answers = conn.execute(
        "SELECT id, entity, asked_at FROM answer_log WHERE action_kind = 'bounce_interface'"
        " AND human_did IS NULL"
    ).fetchall()
    for answer in answers:
        up = conn.execute(
            "SELECT * FROM event WHERE entity = ? AND type = 'admin_up' AND event_time >= ?"
            " ORDER BY event_time LIMIT 1",
            (answer["entity"], answer["asked_at"]),
        ).fetchone()
        if up is None:
            continue
        end = (datetime.fromisoformat(up["event_time"]) + OUTCOME_WINDOW).isoformat()
        samples = conn.execute(
            "SELECT value FROM telemetry WHERE entity = ? AND port = ? AND t >= ? AND t <= ?",
            (up["entity"], up["port"], up["event_time"], end),
        ).fetchall()
        outcome = None
        if samples:
            outcome = (
                "Counters rising afterwards"
                if any(s["value"] > 0 for s in samples)
                else "Counters still at zero afterwards"
            )
        conn.execute(
            "UPDATE answer_log SET human_did = ?, outcome = ? WHERE id = ?",
            (f"Disabled and enabled {up['port']}, seen on the device at {up['event_time']}", outcome, answer["id"]),
        )

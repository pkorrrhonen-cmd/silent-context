"""Who acts: a policy over the agent's answer.

The agent's answer says what to do next. This policy says who does it: the agent itself, a person, or
nobody until someone is asked. It is a small table, read when asked and never stored, and it keeps
the default that the agent proposes and a person acts. The agent itself acts only on a step that is
reversible, that its own log shows was proposed on this class of unit before and carried out with a
good outcome, with no disagreement on record, and with the counters read from the device by the agent.

In this demo the network is synthetic: an action by the agent is an event in the synthetic stream,
and there is no write path to any device. The decision here is real; the execution is not.
"""

import sqlite3
from datetime import datetime

from app.resolve import Graph

REVERSIBLE = {"bounce_interface"}
NAMES = {
    "bounce_interface": "Turning the port off and on",
    "reboot": "A reboot",
    "replace_hw": "A hardware replacement",
    "read": "Reading something",
    "none": "Nothing",
}


def _class_of(graph: Graph, entity: str | None) -> str | None:
    return graph.nodes.get(entity or "", {}).get("class_id")


def _carried_out_on_class(
    conn: sqlite3.Connection, graph: Graph, action_kind: str, entity: str
) -> sqlite3.Row | None:
    """The agent's own record: this step proposed on a unit of this class, done, and the counters rose."""
    rows = conn.execute(
        "SELECT entity, asked_at, human_did, outcome FROM answer_log WHERE action_kind = ?"
        " AND human_did IS NOT NULL AND outcome = 'Counters rising afterwards' ORDER BY asked_at",
        (action_kind,),
    ).fetchall()
    unit_class = _class_of(graph, entity)
    for row in rows:
        if row["entity"] != entity and _class_of(graph, row["entity"]) == unit_class:
            return row
    return None


def who_acts(
    conn: sqlite3.Connection, graph: Graph, decision: dict, entity: str, counters_from: str | None
) -> dict:
    """{"who": "agent" | "person" | "ask", "why": ...} for this answer, from the policy table."""
    tier, kind = decision["tier"], decision["action_kind"]
    if tier == "unknown":
        return {"who": "ask", "why": "The agent does not know. A person on call is asked, and the gap is logged."}
    if tier != "propose":
        return {
            "who": "person",
            "why": "Something must be read or checked first. The agent proposes nothing yet, so nobody acts on its word.",
        }
    if kind not in REVERSIBLE:
        return {
            "who": "person",
            "why": f"{NAMES.get(kind, kind)} is not reversible. The policy keeps it with a person, whatever the evidence.",
        }
    done = _carried_out_on_class(conn, graph, kind, entity)
    if done is None:
        return {
            "who": "person",
            "why": (
                "Reversible, but the agent's own log holds no proposal of this step on this class that a"
                " person carried out with a good outcome. After one, the policy lets the agent act."
            ),
        }
    if counters_from != "telemetry":
        return {
            "who": "person",
            "why": (
                "Reversible and proven on this class, but the counters were reported by a person, not read"
                " from the device by the agent. The policy wants the agent's own reading before it acts."
            ),
        }
    when = datetime.fromisoformat(done["asked_at"]).strftime("%-d.%-m.")
    return {
        "who": "agent",
        "why": (
            f"Reversible; proposed on {done['entity']} on {when}, carried out by a person, and the counters"
            " rose; no disagreement on record; the counters here read from the device by the agent itself."
        ),
    }

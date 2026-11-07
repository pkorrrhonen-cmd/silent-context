"""The agent's calls: `claims_for` and `access_for`.

No model runs here, so an answer works without an endpoint and is the same every time. The tier comes
from rules, the evidence from a template, and the wording of a step from what the expert said. Status
is computed here, for a claim and a unit at this moment, and never stored.
"""

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from app import db, events
from app.resolve import Graph

FALLBACK_GROUP = "transmission-oncall"
BLOCKED_ACTIONS = {"reboot", "replace_hw"}
PROHIBITION = "No reboot or hardware replacement before a failed bounce is reported."
COUNTERS_FRESH_FOR = timedelta(minutes=30)
LEVELS = ("same_node", "same_class", "similar_guess", "none")

STOPWORDS = set(
    "a an and are at be but by for from in is it not no of on or the this that to with after before"
    " still stays stay very".split()
)
# Where a symptom came from says little about what it is, so these words do not count as matching it.
CONTEXT_WORDS = set(
    "sfp replacement replaced replace replacing swap swapped swapping module optical changed change"
    " changing".split()
)

WOULD_CHANGE = {
    "no_claims": "A conversation or email about this symptom on this unit or its class.",
    "entity_unclear": "An identifier that names a known unit.",
    "not_applicable": "A statement that this advice also covers this unit, or a symptom that fits it.",
    "superseded": "A newer statement that still holds.",
}


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.casefold())
    return {_stem(word) for word in words if word not in STOPWORDS | CONTEXT_WORDS}


def symptom_matches(query: str, *claim_texts: str | None) -> bool:
    """A plain word match over what the claim says, not a judgement of meaning.

    Both ways of being wrong are cheap: a miss says "I don't know", and a false match still has to pass
    the claim's own check before anything is proposed.
    """
    wanted = _tokens(query)
    have = set().union(*(_tokens(text or "") for text in claim_texts)) if claim_texts else set()
    if not wanted:
        return False
    overlap = len(wanted & have)
    return overlap >= min(2, len(wanted)) and overlap / len(wanted) > 0.5


def _clock(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT value FROM meta WHERE key = 'as_of'").fetchone()
    return row["value"] if row and row["value"] else datetime.now().isoformat(timespec="seconds")


def _age_days(received_at: str, now: str) -> int:
    return (datetime.fromisoformat(now) - datetime.fromisoformat(received_at)).days


def _read_counters(conn: sqlite3.Connection, entity: str, now: str) -> str:
    """What the agent can see for itself: the newest sample, if it is recent enough to mean anything."""
    row = conn.execute(
        "SELECT t, value FROM telemetry WHERE entity = ? AND t <= ? ORDER BY t DESC LIMIT 1",
        (entity, now),
    ).fetchone()
    if row is None:
        return "unknown"
    if datetime.fromisoformat(now) - datetime.fromisoformat(row["t"]) > COUNTERS_FRESH_FOR:
        return "unknown"
    return "rising" if row["value"] > 0 else "zero"


def _observations(conn: sqlite3.Connection, entity: str, observed: dict | None, now: str) -> dict:
    seen = observed or {}
    counters = seen.get("counters") or "unknown"
    source = "reported" if counters != "unknown" else None
    if counters == "unknown":
        counters = _read_counters(conn, entity, now)
        source = "telemetry" if counters != "unknown" else None
    return {
        "link": seen.get("link") or "unknown",
        "counters": counters,
        "counters_from": source,
        "bounce_done": bool(seen.get("bounce_done")),
        "bounce_failed": bool(seen.get("bounce_failed")),
    }


# What a claim is to this unit


@dataclass(frozen=True)
class Candidate:
    claim: sqlite3.Row
    level: str
    status: str
    status_note: str | None


def _class_of(graph: Graph, entity: str | None) -> str | None:
    return graph.nodes.get(entity or "", {}).get("class_id")


def _match_level(graph: Graph, entity: str, claim: sqlite3.Row) -> str:
    if claim["observed_entity"] == entity:
        return "same_node"
    unit_class = _class_of(graph, entity)
    if claim["scope_status"] == "confirmed":
        return "same_class" if claim["applies_to"] == unit_class else "none"
    if _class_of(graph, claim["observed_entity"]) == unit_class:
        return "same_class"
    return "similar_guess"


def _conflict_partners(conn: sqlite3.Connection, claim_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT src, dst FROM edge WHERE rel = 'CONFLICTS_WITH' AND (src = ? OR dst = ?)",
        (claim_id, claim_id),
    ).fetchall()
    return [row["dst"] if row["src"] == claim_id else row["src"] for row in rows]


def _status(
    conn: sqlite3.Connection, claim: sqlite3.Row, level: str, entity: str, at: str | None
) -> tuple[str, str | None]:
    """This claim's status for this unit, and why, when there is more to say than the status."""
    if claim["superseded_at"]:
        return "superseded", None
    if level == "none":
        return "not_applicable", None
    doubt = events.recheck(conn, claim, entity, at)
    if _conflict_partners(conn, claim["id"]):
        return "disputed", doubt[1] if doubt else None
    return doubt if doubt else ("active", None)


def _candidates(
    conn: sqlite3.Connection, graph: Graph, entity: str, symptom: str, at: str | None
) -> list[Candidate]:
    """Bound claims only: a waiting claim is never offered as being about a particular unit."""
    rows = conn.execute(
        "SELECT * FROM claim WHERE kind = 'troubleshooting' AND binding_status = 'bound'"
    ).fetchall()
    found = []
    for claim in rows:
        if not symptom_matches(symptom, claim["symptom"], claim["check_step"], claim["claim_text"]):
            continue
        if at and claim["valid_from"] and claim["valid_from"] > at:
            continue
        level = _match_level(graph, entity, claim)
        status, status_note = _status(conn, claim, level, entity, at)
        found.append(Candidate(claim, level, status, status_note))
    found.sort(key=lambda c: (LEVELS.index(c.level), c.claim["received_at"], c.claim["id"]))
    return found


def _match_note(graph: Graph, entity: str, candidate: Candidate) -> str:
    claim, level = candidate.claim, candidate.level
    observed, scope = claim["observed_entity"], claim["scope_text"]
    if level == "same_node":
        return f"Observed on {entity}."
    if level == "same_class" and claim["scope_status"] == "confirmed":
        return f'Observed on {observed}. The teller says it covers "{scope}", and {entity} is in that class.'
    if level == "same_class":
        return (
            f'Observed on {observed}. {entity} is the same class, but the scope "{scope}" is undefined,'
            " so reaching this unit is an inference."
        )
    if level == "similar_guess":
        return f"A guess: observed on {observed}, a different class from {entity}, and the scope is undefined."
    return f'Not for this unit: the teller says it covers "{scope}", and {entity} is in another class.'


def _outcomes_in_class(
    conn: sqlite3.Connection, graph: Graph, claim_id: str, entity: str
) -> tuple[bool, bool]:
    # Telemetry is left out: linking a rise to the advice is a suggestion, not something reported.
    rows = conn.execute(
        "SELECT type, scope_entity FROM evidence_event WHERE claim_id = ? AND basis = 'message'"
        " AND type IN ('reported_success', 'reported_failure')",
        (claim_id,),
    ).fetchall()
    in_class = [r for r in rows if _class_of(graph, r["scope_entity"]) == _class_of(graph, entity)]
    return (
        any(r["type"] == "reported_success" for r in in_class),
        any(r["type"] == "reported_failure" for r in in_class),
    )


# The tier


def _decision(tier: str, next_step: str, action_kind: str, would_change: str, **rest) -> dict:
    return {
        "tier": tier,
        "next_step": next_step,
        "action_kind": action_kind,
        "what_would_change": would_change,
        "prohibition": rest.get("prohibition"),
        "reason_code": rest.get("reason_code"),
    }


def _decide(
    claim: sqlite3.Row,
    level: str,
    status: str,
    status_note: str | None,
    entity: str,
    success: bool,
    failure: bool,
    seen: dict,
) -> dict:
    check = claim["check_step"] or claim["action"] or claim["claim_text"]
    action_kind = claim["action_kind"]
    bounces = action_kind == "bounce_interface"
    held_back = PROHIBITION if bounces else None
    counters_would_change = (
        f"The counters on {entity}: at zero this becomes a proposal, and rising means it does not fit."
    )

    if status == "disputed":
        return _decision(
            "check_first",
            "Read the traffic counters first. The recorded advice disagrees on what comes next, and"
            " this answer does not choose.",
            "read",
            "A reported outcome on this class after the disagreement.",
        )
    if seen["bounce_failed"] and bounces:
        return _decision(
            "propose",
            "The bounce is reported as failed, so this advice no longer holds back a reboot or a"
            " hardware replacement. It says nothing beyond that.",
            "reboot",
            "Nothing recorded goes further than this.",
        )
    if seen["bounce_done"] and bounces:
        if seen["counters"] == "rising":
            return _decision(
                "check_first",
                "The counters are rising after the bounce. This advice asks nothing more.",
                "none",
                "The counters falling back to zero.",
            )
        return _decision(
            "check_first",
            "Read the counters and report whether traffic came back after the bounce.",
            "read",
            "A report that the bounce failed, which lifts the prohibition.",
            prohibition=held_back,
        )
    if status in ("recheck", "order_unknown"):
        return _decision(
            "check_first",
            f"{check.rstrip('.')}. {status_note}",
            "read",
            f"A reported success on {entity} after that change, or a newer statement.",
            prohibition=held_back,
        )

    if claim["check_kind"] == "read_counters":
        if seen["counters"] == "rising" or seen["link"] == "down":
            return _decision(
                "unknown",
                "This advice does not fit what is observed here.",
                "none",
                "An observation of zero counters on a link that is up.",
                reason_code="not_applicable",
            )
        condition_met = seen["counters"] == "zero"
    else:
        condition_met = claim["check_kind"] is None

    if action_kind in ("read", "none"):
        return _decision(
            "check_first",
            claim["action"] or check,
            "read" if action_kind == "read" else "none",
            "A reported outcome that gives a concrete action.",
        )
    if level == "similar_guess":
        return _decision(
            "check_first",
            check,
            "read",
            "A statement that this advice also covers this class.",
            prohibition=held_back,
        )
    if not condition_met:
        return _decision("check_first", check, "read", counters_would_change, prohibition=held_back)
    if failure or not success:
        reason = "A failure is reported on this class." if failure else "It has only been told so far."
        return _decision(
            "check_first",
            f"{check.rstrip('.')}. {reason}",
            "read",
            "A reported success on this class.",
            prohibition=held_back,
        )
    decision = _decision(
        "propose",
        claim["action"] or check,
        action_kind,
        "A report that this failed, which lifts the prohibition."
        if bounces
        else "A reported failure on this class.",
        prohibition=held_back,
    )
    if action_kind in BLOCKED_ACTIONS and not seen["bounce_failed"]:
        return _decision(
            "check_first", check, "read", "A report that a bounce failed.", prohibition=PROHIBITION
        )
    return decision


# What is shown


def render_evidence(conn: sqlite3.Connection, claim: sqlite3.Row, now: str) -> str:
    """From a template, never from a model, so no count or strength can appear that nobody reported."""
    lines = [f"Scope: {claim['scope_text'] or 'not stated'} ({claim['scope_status']})"]
    reported = conn.execute(
        "SELECT * FROM evidence_event WHERE claim_id = ? AND type != 'told'"
        " ORDER BY event_time IS NULL, event_time, id",
        (claim["id"],),
    ).fetchall()
    for event in reported:
        excerpt = " ".join((event["excerpt"] or "").split())
        quote = f' · "{excerpt}"' if excerpt else ""
        if event["basis"] == "telemetry":
            lines.append(
                f"Observed: {event['event_time']} · counters rising · {event['scope_entity']}{quote}"
                " · source telemetry"
            )
            continue
        lines.append(
            f"Reported: {event['event_time'] or 'time unknown'} · {event['type']}"
            f" · {event['scope_entity'] or 'no unit'}{quote}"
            f" · source {event['channel']}/{event['role'] or 'role unknown'}"
        )
    told_refs = {
        row["source_ref"]
        for row in conn.execute(
            "SELECT source_ref FROM evidence_event WHERE claim_id = ? AND type = 'told'",
            (claim["id"],),
        )
    }
    sources = conn.execute(
        "SELECT * FROM source WHERE claim_id = ? ORDER BY received_at, id", (claim["id"],)
    ).fetchall()
    tellers: dict[str, list[sqlite3.Row]] = {}
    for source in sources:
        tellers.setdefault(source["teller_key"], []).append(source)
    for group in tellers.values():
        kind = "Told" if any(s["ref"] in told_refs for s in group) else "Relayed"
        channels = list(dict.fromkeys(f"{s['channel']}/{s['role'] or 'role unknown'}" for s in group))
        lines.append(
            f"{kind}: {group[0]['source_time_text'] or 'time unknown'} · {', '.join(channels)}"
            f" · received {group[0]['received_at']}"
        )
    confirmed = conn.execute(
        "SELECT max(event_time) AS last FROM evidence_event"
        " WHERE claim_id = ? AND type = 'reported_success' AND basis = 'message'",
        (claim["id"],),
    ).fetchone()["last"]
    lines.append(
        f"Information age: {_age_days(claim['received_at'], now)} days (validity start"
        f" {claim['valid_from'] or 'unknown'}, last confirmed {confirmed or 'never'})"
    )
    return "\n".join(lines)


def _view(
    conn: sqlite3.Connection,
    claim: sqlite3.Row,
    status: str,
    level: str,
    note: str,
    now: str,
    status_note: str | None = None,
) -> dict:
    evidence = conn.execute(
        "SELECT type, scope_entity, event_time, source_ref, excerpt, basis FROM evidence_event"
        " WHERE claim_id = ? ORDER BY event_time IS NULL, event_time, id",
        (claim["id"],),
    ).fetchall()
    sources = conn.execute(
        "SELECT channel, role, ref FROM source WHERE claim_id = ? ORDER BY received_at, id",
        (claim["id"],),
    ).fetchall()
    return {
        "id": claim["id"],
        "kind": claim["kind"],
        "action_kind": claim["action_kind"],
        "claim_text": claim["claim_text"],
        "symptom": claim["symptom"],
        "observed_entity": claim["observed_entity"],
        "binding_status": claim["binding_status"],
        "binding_reason": claim["binding_reason"],
        "received_at": claim["received_at"],
        "valid_from_basis": claim["valid_from_basis"],
        "superseded_at": claim["superseded_at"],
        "scope_text": claim["scope_text"],
        "scope_status": claim["scope_status"],
        "status_for_entity": status,
        "status_note": status_note,
        "match_level": level,
        "match_note": note,
        "info_age_days": _age_days(claim["received_at"], now),
        "valid_from": claim["valid_from"],
        "valid_to": claim["valid_to"],
        "valid_to_basis": claim["valid_to_basis"],
        "evidence": [
            {
                "type": e["type"],
                "scope": e["scope_entity"],
                "event_time": e["event_time"],
                "source_ref": e["source_ref"],
                "excerpt": e["excerpt"],
                "basis": e["basis"],
            }
            for e in evidence
        ],
        "sources": [{"channel": s["channel"], "role": s["role"], "link": s["ref"]} for s in sources],
        "evidence_rendered": render_evidence(conn, claim, now),
    }


def _log(
    conn: sqlite3.Connection,
    now: str,
    entity: str,
    symptom: str,
    tier: str,
    next_step: str,
    action_kind: str,
    claim_ids: list[str],
    group: str | None,
) -> str:
    answer_id = f"ans-{uuid4().hex[:12]}"
    conn.execute(
        "INSERT INTO answer_log (id, asked_at, entity, symptom, tier, next_step, action_kind,"
        " claim_ids) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (answer_id, now, entity, symptom, tier, next_step, action_kind, json.dumps(claim_ids)),
    )
    if tier == "unknown":
        conn.execute(
            "INSERT INTO gap_log (id, asked_at, entity, symptom, ask_group) VALUES (?, ?, ?, ?, ?)",
            (f"gap-{uuid4().hex[:12]}", now, entity, symptom, group),
        )
    return answer_id


def list_claims(conn: sqlite3.Connection) -> list[dict]:
    """Every known claim, with its status apart from any particular unit."""
    now = _clock(conn)
    views = []
    for claim in conn.execute("SELECT * FROM claim ORDER BY received_at, id").fetchall():
        if claim["binding_status"] == "waiting":
            status = "waiting"
        elif claim["superseded_at"]:
            status = "superseded"
        elif _conflict_partners(conn, claim["id"]):
            status = "disputed"
        else:
            status = "active"
        views.append(_view(conn, claim, status, "", "", now))
    return views


def claims_for(
    entity_id: str,
    symptom: str,
    at: str | None = None,
    observed: dict | None = None,
    *,
    conn: sqlite3.Connection | None = None,
) -> dict:
    """What is known about this unit and symptom, and what to do next.

    `at` is a point in world time. `observed` is what someone reports: link (up, down, unknown),
    counters (rising, zero, unknown), bounce_done and bounce_failed. Counters nobody reported are read
    from telemetry when a recent sample exists.
    """
    if conn is None:
        with db.session() as own:
            return claims_for(entity_id, symptom, at, observed, conn=own)

    graph = Graph.load(conn)
    now = _clock(conn)
    known_unit = entity_id in graph.nodes
    attrs = graph.nodes.get(entity_id, {})
    group = attrs.get("responsible_group", FALLBACK_GROUP)
    seen = _observations(conn, entity_id, observed, now)
    used = {"counters": seen["counters"], "counters_from": seen["counters_from"]}

    candidates = _candidates(conn, graph, entity_id, symptom, at) if known_unit else []
    usable = [c for c in candidates if c.status not in ("not_applicable", "superseded")]

    if usable:
        primary = usable[0]
        success, failure = _outcomes_in_class(conn, graph, primary.claim["id"], entity_id)
        decision = _decide(
            primary.claim,
            primary.level,
            primary.status,
            primary.status_note,
            entity_id,
            success,
            failure,
            seen,
        )
        match_level = primary.level
        # A guess is only worth showing when nothing better exists.
        shown = [c for c in candidates if c.level != "similar_guess" or c is primary]
    else:
        reason = (
            "entity_unclear"
            if not known_unit
            else "no_claims"
            if not candidates
            else candidates[0].status
        )
        decision = _decision(
            "unknown", f"Ask {group}.", "none", WOULD_CHANGE[reason], reason_code=reason
        )
        match_level = "none"
        shown = candidates

    views = [
        _view(conn, c.claim, c.status, c.level, _match_note(graph, entity_id, c), now, c.status_note)
        for c in shown
    ]
    listed = {view["id"] for view in views}
    for candidate in shown:
        for partner_id in _conflict_partners(conn, candidate.claim["id"]):
            if partner_id not in listed:
                listed.add(partner_id)
                partner = conn.execute("SELECT * FROM claim WHERE id = ?", (partner_id,)).fetchone()
                bound = partner["binding_status"] == "bound"
                note = (
                    f"Disagrees with the claim above. Observed on {partner['observed_entity']}."
                    if bound
                    else "Disagrees with the claim above. Not bound to a unit, so it is shown as the"
                    " reason for the disagreement and not offered as advice for this unit."
                )
                views.append(_view(conn, partner, "disputed", "none", note, now))

    ask_group = group if decision["tier"] == "unknown" else None
    answer_id = _log(
        conn,
        now,
        entity_id,
        symptom,
        decision["tier"],
        decision["next_step"],
        decision["action_kind"],
        [view["id"] for view in views],
        ask_group,
    )
    return {
        **decision,
        "match_level": match_level,
        "match_note": views[0]["match_note"] if views else None,
        "claims": views,
        "evidence_rendered": "\n\n".join(view["evidence_rendered"] for view in views),
        "ask_group": ask_group,
        "observed_used": used,
        "answer_id": answer_id,
    }


def access_for(
    place: str, at: str | None = None, *, conn: sqlite3.Connection | None = None
) -> dict:
    """How to reach a place, before anyone drives there. A node counts as the site it stands at.

    With `at`, what held at that point in world time. If the moment a claim stopped holding is unknown,
    both claims may hold, and the answer says that the boundary is not known.
    """
    if conn is None:
        with db.session() as own:
            return access_for(place, at, conn=own)

    graph = Graph.load(conn)
    now = _clock(conn)
    site = graph.site_of_node.get(place) or (place if place in graph.site_aliases.values() else None)
    if site is None:
        answer_id = _log(conn, now, place, "access", "unknown", f"Ask {FALLBACK_GROUP}.", "none", [], FALLBACK_GROUP)
        return {
            "site": None,
            "tier": "unknown",
            "next_step": f"Ask {FALLBACK_GROUP}.",
            "claims": [],
            "boundary_known": True,
            "evidence_rendered": "",
            "what_would_change": WOULD_CHANGE["entity_unclear"],
            "ask_group": FALLBACK_GROUP,
            "reason_code": "entity_unclear",
            "answer_id": answer_id,
        }

    group = next(
        (
            attrs["responsible_group"]
            for row in conn.execute("SELECT id, attrs FROM entity WHERE id = ?", (site,))
            for attrs in [json.loads(row["attrs"])]
            if "responsible_group" in attrs
        ),
        FALLBACK_GROUP,
    )
    targets = [site, *graph.barriers_of_site.get(site, [])]
    marks = ",".join("?" for _ in targets)
    rows = conn.execute(
        f"SELECT * FROM claim WHERE kind = 'access' AND binding_status = 'bound'"
        f" AND observed_entity IN ({marks}) ORDER BY received_at DESC, id DESC",
        targets,
    ).fetchall()

    def holds(claim: sqlite3.Row) -> bool:
        if at is None:
            return claim["superseded_at"] is None
        if claim["valid_from"] and claim["valid_from"] > at:
            return False
        return not (claim["valid_to"] and claim["valid_to"] <= at)

    holding = [claim for claim in rows if holds(claim)]
    boundary_known = len(holding) <= 1

    def status_at(claim: sqlite3.Row) -> str:
        if claim in holding:
            return "active"
        return "superseded" if claim["superseded_at"] else "not_yet_valid"

    views = [
        _view(
            conn,
            claim,
            status_at(claim),
            "same_node",
            "May hold at this time; the boundary is not known."
            if not boundary_known and claim in holding
            else "",
            now,
        )
        for claim in [*holding, *(c for c in rows if c not in holding)]
    ]
    tier = "propose" if holding else "unknown"
    next_step = (
        holding[0]["claim_text"]
        if len(holding) == 1
        else "The recorded statements below may both hold at this time, and the moment one replaced"
        " the other is not known."
        if holding
        else f"Ask {group}."
    )
    ask_group = None if holding else group
    answer_id = _log(conn, now, place, "access", tier, next_step, "none", [v["id"] for v in views], ask_group)
    return {
        "site": site,
        "tier": tier,
        "next_step": next_step,
        "claims": views,
        "boundary_known": boundary_known,
        "evidence_rendered": "\n\n".join(
            view["evidence_rendered"] for view in views if view["status_for_entity"] != "not_yet_valid"
        ),
        "what_would_change": "A newer statement about how to reach this place.",
        "ask_group": ask_group,
        "reason_code": None if holding else "no_claims",
        "answer_id": answer_id,
    }

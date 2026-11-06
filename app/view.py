"""What the page shows: the whole state at the demo clock, in one call."""

import hashlib
import json
import sqlite3
from pathlib import Path

from app import claims, export, ingest
from app.sources import ROOT, SOURCES_DIR, load_manifest, parse

REPEATS_FILE = ROOT / "data" / "truth" / "held_out_repeats.json"


def _sources(conn: sqlite3.Connection) -> list[dict]:
    logged = {row["file"]: row for row in conn.execute("SELECT * FROM ingest_log")}
    views = []
    for entry in load_manifest()["sources"]:
        log = logged.get(entry["file"])
        views.append(
            {
                "file": entry["file"],
                "channel": entry["channel"],
                "origin": entry["origin"],
                "received_at": entry["received_at"],
                "known": log is not None,
                "sha256": log["sha256"] if log else None,
                "unchanged": log["sha256"] == entry["sha256"] if log and "sha256" in entry else None,
                "claim_ids": json.loads(log["claim_ids"]) if log else [],
                "mode": log["mode"] if log else None,
            }
        )
    return views


def _events(as_of: str | None) -> list[dict]:
    stream = json.loads(ingest.EVENTS_FILE.read_text(encoding="utf-8"))["events"]
    return [{**event, "known": not as_of or event["event_time"] <= as_of} for event in stream]


def _metrics(conn: sqlite3.Connection) -> dict:
    count = lambda sql: conn.execute(sql).fetchone()[0]
    groups = {
        row["ask_group"]: row["n"]
        for row in conn.execute(
            "SELECT ask_group, count(*) AS n FROM gap_log GROUP BY ask_group ORDER BY ask_group"
        )
    }
    repeats = json.loads(REPEATS_FILE.read_text(encoding="utf-8")) if REPEATS_FILE.exists() else None
    return {
        # Both are zero by construction: no module here can post to any channel, and a test holds that.
        "conversations_started": 0,
        "actions_asked_of_specialists": 0,
        "sources_read": count("SELECT count(*) FROM ingest_log"),
        "bound": count("SELECT count(*) FROM claim WHERE binding_status = 'bound'"),
        "waiting": count("SELECT count(*) FROM claim WHERE binding_status = 'waiting'"),
        "gaps_by_group": groups,
        "held_out_wrong_per_run": repeats["confident_wrong_per_run"] if repeats else None,
        "held_out_distinct_wrong_files": len(repeats["distinct_wrong_files"]) if repeats else None,
    }


def state(conn: sqlite3.Connection) -> dict:
    row = conn.execute("SELECT value FROM meta WHERE key = 'as_of'").fetchone()
    as_of = (row["value"] or None) if row else None
    log = conn.execute(
        "SELECT entity, asked_at, next_step, human_did, outcome FROM answer_log"
        " WHERE human_did IS NOT NULL ORDER BY asked_at DESC LIMIT 3"
    ).fetchall()
    return {
        "as_of": as_of,
        "started": row is not None,
        "sources": _sources(conn),
        "events": _events(as_of),
        "claims": claims.list_claims(conn),
        "graph": export.graph(conn),
        "metrics": _metrics(conn),
        "log": [dict(line) for line in log],
    }


def source(file: str) -> dict | None:
    """One source as it was read. Only files the manifest lists can be asked for."""
    entry = next((e for e in load_manifest()["sources"] if e["file"] == file), None)
    if entry is None:
        return None
    path: Path = SOURCES_DIR / entry["file"]
    thread = parse(path, entry["file"])
    return {
        "file": entry["file"],
        "channel": thread.channel,
        "origin": entry["origin"],
        "original_name": entry.get("original_name"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "subject": thread.subject,
        "date_text": thread.date_text,
        "messages": [
            {"seq": m.seq, "time": m.time, "author": m.author, "role": m.role, "text": m.text}
            for m in thread.messages
        ],
    }

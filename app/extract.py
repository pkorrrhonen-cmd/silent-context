"""What the model is asked, and its recorded answers.

The model reads a thread and reports what it says. It does not decide which entity a claim is bound
to, what time it holds from or how sure anyone should be: code does that from what the model copies
out of the text (`app/resolve.py`, `app/ingest.py`).

Every answer is recorded next to the data, keyed by the whole prompt. A rerun needs no model and no
key as long as nothing it depends on has changed, and the demo can run without any endpoint.
"""

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app import llm
from app.sources import ROOT, Thread

EXTRACTIONS_DIR = ROOT / "data" / "extractions"

SYSTEM_PROMPT = """\
You read conversations and emails from a telecom network operations team and extract what \
specialists know, so that an agent can use it in a later case.

Nobody reviews your output before it is stored. A claim bound to the wrong unit can send an engineer \
the wrong way, so report only what the text supports, and leave a field empty when the text does not \
say. An empty field is a good result: it keeps the claim waiting instead of guessing.

## What a claim is

Advice or knowledge someone could use again: how to read a symptom, what to do and in what order, \
what not to do, where a key is, how to reach a site. These are not claims: schedules, status reports, \
complaints, small talk, and a plain account of what was done that offers nothing to reuse. If the \
thread holds no claim, return an empty list.

Advice for one problem is one claim, even when it is spread over several messages: how to read the \
symptom, what to check, what to do and what not to do belong together, because the agent needs them \
together. Split only when a part can be used on its own for a different problem. If two people give \
opposing advice, that is two claims.

## Claim fields

kind: "access" for how to reach or enter a place, otherwise "troubleshooting".

claim_text: one or two sentences in the speaker's terms. Keep the order of steps, what not to do, and \
hedging words such as "sometimes", "usually" and "probably". Never sound more certain than the speaker.

symptom: the situation the advice is for, as a short phrase. Null when it is not about a symptom.

advice_message_seqs: the seq numbers of the messages where this person gives this advice. All of them \
come from one person.

relayed: true when that person is passing on someone else's advice rather than speaking from their \
own knowledge, for example "Maija told us to try this first".

target_node_ids, target_sites, target_ports: the identifiers the thread uses for the very unit or place \
this advice concerns, copied exactly as written. A unit named earlier about something else does not \
count, and neither does a unit named only as a comparison. If the thread does not make clear which \
unit this advice concerns, leave these empty.

target_firmware: the firmware version the thread states for that same unit, as written. Otherwise null.

mentions_barrier: true when the claim is about getting past a barrier or a gate on the way to a site.

procedure_type: the id from the list of known procedures when the advice is tied to that procedure. \
Otherwise null.

scope_text: the speaker's own words for which units the advice covers, copied exactly, for example \
"the rack-mounted ones". Do not turn them into an age limit or a year. Null when the speaker says \
nothing about it.

scope_names_version: when those words name a firmware version or a model, that version or model as \
written. Otherwise null.

relative_time: for a claim about how things stand now, the words that say when this became true \
relative to the message, copied exactly, for example "last Friday". Do not convert them to a date. \
Null when the message does not say.

## Claims already known

Use these when the request lists known claims. A claim has at most one of the three.

same_as_existing: the id of a known claim when this is the same advice, even when it is told in \
another channel, repeated or relayed. Still fill advice_message_seqs and outcomes. Fill scope_text \
only if the message narrows what the advice covers.

replaces_existing: the id of a known claim when this message says explicitly that the earlier state of \
things has changed.

contradicts_existing: the id of a known claim when this advice opposes it and neither side gives way.

## Outcomes

outcomes: a specific event in this thread where someone tried this advice and says what happened. \
kind is "success" when following the advice worked and "failure" when they followed it and it did not \
help. message_seq is the message that reports it. unit_id is the identifier of the unit it happened \
on, as written, or null.

These are not outcomes: a general statement such as "this has solved it many times", which is part \
of the telling, and a recovery the thread puts down to something else.

## Estimates

estimates: when someone estimates a unit's installation year. value_text is their words, copied \
exactly, for example "around 2015". entity_id is the unit's identifier and message_seq the message.
"""


class Outcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["success", "failure"]
    message_seq: int
    unit_id: str | None


class Estimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str | None
    attribute: Literal["installed_year"]
    value_text: str
    message_seq: int


class ExtractedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["troubleshooting", "access"]
    claim_text: str
    symptom: str | None
    advice_message_seqs: list[int]
    relayed: bool
    target_node_ids: list[str]
    target_sites: list[str]
    target_ports: list[str]
    target_firmware: str | None
    mentions_barrier: bool
    procedure_type: str | None
    scope_text: str | None
    scope_names_version: str | None
    relative_time: str | None
    same_as_existing: str | None
    replaces_existing: str | None
    contradicts_existing: str | None
    outcomes: list[Outcome]


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claims: list[ExtractedClaim]
    estimates: list[Estimate]


def _render_thread(thread: Thread) -> str:
    if thread.channel == "email":
        message = thread.messages[0]
        return (
            f"An email, message seq 1.\nFrom: {message.author}\n"
            f"Date: {thread.date_text or 'not given'}\nSubject: {thread.subject}\n\n{message.text}"
        )
    lines = [f"A Teams conversation. Date: {thread.date_text or 'not given'}."]
    lines += [
        f"[seq {m.seq} | {m.time} | {m.role}] {m.author}: {m.text}" for m in thread.messages
    ]
    return "\n".join(lines)


def build_request(thread: Thread, known_claims: str, procedures: str) -> str:
    return (
        f"Known procedures:\n{procedures}\n\n"
        f"Known claims:\n{known_claims or 'None yet.'}\n\n"
        f"The thread:\n{_render_thread(thread)}"
    )


def cache_file_for(cache_dir: Path, file: str) -> Path:
    return cache_dir / f"{file.replace('/', '__')}.json"


def extract(
    thread: Thread,
    known_claims: str,
    procedures: str,
    cache_dir: Path = EXTRACTIONS_DIR,
    refresh: bool = False,
) -> tuple[Extraction, str]:
    """The model's answer for a thread, and whether it came from the record or from the model."""
    request = build_request(thread, known_claims, procedures)
    schema = Extraction.model_json_schema()
    key = hashlib.sha256(
        "\n".join([SYSTEM_PROMPT, json.dumps(schema, sort_keys=True), request]).encode("utf-8")
    ).hexdigest()
    cache_file = cache_file_for(cache_dir, thread.file)
    if cache_file.exists() and not refresh:
        recorded = json.loads(cache_file.read_text(encoding="utf-8"))
        if recorded["key"] == key:
            return Extraction.model_validate(recorded["output"]), "recorded"
    output = llm.complete_json(SYSTEM_PROMPT, request, "extraction", schema)
    extraction = Extraction.model_validate(output)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps(
            {"key": key, "model": llm.model_name(), "output": extraction.model_dump()},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return extraction, "model"

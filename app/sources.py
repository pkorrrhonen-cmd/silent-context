"""Reads the sources as they are: Teams exports, emails and ticket exports become one shape, a thread of messages."""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT / "data" / "sources"
MANIFEST_FILE = SOURCES_DIR / "manifest.json"

EMAIL_DATE_FORMAT = "%a, %d %b %Y %H:%M"
HEADER = re.compile(r"^(From|To|Date|Subject):\s*(.*)$")


@dataclass(frozen=True)
class Message:
    seq: int
    time: str | None
    author: str | None
    role: str | None
    text: str


@dataclass(frozen=True)
class Thread:
    file: str
    channel: str
    day: str | None
    date_text: str | None
    subject: str | None
    messages: tuple[Message, ...]

    def message(self, seq: int) -> Message | None:
        return next((m for m in self.messages if m.seq == seq), None)

    def full_text(self) -> str:
        return "\n".join([self.subject or "", *(m.text for m in self.messages)])

    def source_time_text(self) -> str | None:
        """The source's own time, as written. Nothing is added to it."""
        if self.channel == "email":
            return self.date_text
        times = [m.time for m in self.messages if m.time]
        if not times:
            return None
        return times[0] if len(times) == 1 else f"{times[0]} to {times[-1]}"


def appears_in(needle: str, text: str) -> bool:
    """Whether a phrase is literally in the text, ignoring case and line breaks."""
    squeeze = lambda s: " ".join(s.split()).casefold()
    return bool(needle.strip()) and squeeze(needle) in squeeze(text)


def _parse_teams(path: Path, file: str) -> Thread:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Thread(
        file=file,
        channel="teams",
        day=data.get("date"),
        date_text=data.get("date"),
        subject=None,
        messages=tuple(
            Message(m["seq"], m.get("time"), m.get("author"), m.get("role"), m["text"])
            for m in data["messages"]
        ),
    )


def _parse_email(path: Path, file: str) -> Thread:
    lines = path.read_text(encoding="utf-8").splitlines()
    headers: dict[str, str] = {}
    body_start = 0
    for index, line in enumerate(lines):
        match = HEADER.match(line)
        if not match:
            body_start = index
            break
        headers[match.group(1)] = match.group(2).strip()
    date_text = headers.get("Date")
    day = time = None
    if date_text:
        try:
            parsed = datetime.strptime(date_text, EMAIL_DATE_FORMAT)
        except ValueError:
            pass
        else:
            day, time = parsed.strftime("%Y-%m-%d"), parsed.strftime("%H:%M")
    return Thread(
        file=file,
        channel="email",
        day=day,
        date_text=date_text,
        subject=headers.get("Subject"),
        messages=(
            Message(1, time, headers.get("From"), None, "\n".join(lines[body_start:]).strip()),
        ),
    )


def _parse_ticket(path: Path, file: str) -> Thread:
    """A ticketing system's export: the title and the worklog, one entry per message. Same shape, same reader."""
    data = json.loads(path.read_text(encoding="utf-8"))
    day = (data.get("opened") or "")[:10] or None
    return Thread(
        file=file,
        channel="ticket",
        day=day,
        date_text=data.get("opened"),
        subject=f"{data.get('ticket', '')} {data.get('title', '')}".strip() or None,
        messages=tuple(
            Message(m["seq"], m.get("time"), m.get("author"), m.get("role"), m["text"])
            for m in data["worklog"]
        ),
    )


def parse(path: Path, file: str) -> Thread:
    if path.suffix != ".json":
        return _parse_email(path, file)
    data = json.loads(path.read_text(encoding="utf-8"))
    return _parse_ticket(path, file) if "worklog" in data else _parse_teams(path, file)


def load_manifest() -> dict:
    return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

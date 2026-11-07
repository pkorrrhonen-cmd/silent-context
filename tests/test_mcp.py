"""The MCP wrapper: the agent's calls as tools, answering as the functions behind the HTTP interface do."""

import json
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from app import claims, ingest, mcp_server

AFTER_CAPTURE = "2026-10-20T12:00:00"
SYMPTOM = "Link up, counters zero after SFP replacement"


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = ingest.run(tmp_path / "store.db", until=AFTER_CAPTURE)
    monkeypatch.setenv("STORE_PATH", str(path))
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    return path


async def _session(calls: list[tuple[str, dict]]) -> tuple[list[str], list]:
    """Tool names and the results of the calls, over an in-memory transport to the same server."""
    low = mcp_server.server._lowlevel_server
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        async with anyio.create_task_group() as tg:
            tg.start_soon(low.run, server_streams[0], server_streams[1], low.create_initialization_options())
            async with ClientSession(*client_streams) as session:
                await session.initialize()
                names = sorted(tool.name for tool in (await session.list_tools()).tools)
                results = [await session.call_tool(name, args) for name, args in calls]
            tg.cancel_scope.cancel()
    return names, results


def test_the_tools_answer_as_the_functions_do(store: Path) -> None:
    names, (answer, access, thread, missing) = anyio.run(
        _session,
        [
            ("claims_for", {"entity": "TRN-051", "symptom": SYMPTOM, "counters": "zero"}),
            ("access_for", {"place": "SITE-NILO"}),
            ("source", {"file": "teams_trn042.json"}),
            ("source", {"file": "../.env"}),
        ],
    )
    assert names == ["access_for", "claims_for", "source"]

    assert not answer.is_error
    got = answer.structured_content
    direct = claims.claims_for("TRN-051", SYMPTOM, None, {"counters": "zero"})
    assert got["tier"] == direct["tier"] == "propose"
    assert got["next_step"] == direct["next_step"]
    assert got["prohibition"] == claims.PROHIBITION
    assert [c["id"] for c in got["claims"]] == [c["id"] for c in direct["claims"]]
    assert json.loads(answer.content[0].text)["tier"] == "propose"

    assert not access.is_error
    assert "grey box" in access.structured_content["next_step"]

    assert not thread.is_error
    assert thread.structured_content["file"] == "teams_trn042.json"
    assert thread.structured_content["messages"][0]["author"]

    assert missing.is_error
    assert "not a source in the manifest" in missing.content[0].text


def test_the_wrapper_only_reads_and_answers() -> None:
    """No module of the wrapper can post anywhere: the same promise the page's zeros make."""
    text = (Path(mcp_server.__file__)).read_text(encoding="utf-8")
    for word in ("requests", "httpx", "smtplib", "urlopen", "subprocess"):
        assert word not in text

"""The agent's calls as MCP tools, so an MCP client can ask the store directly.

    uv run python -m app.mcp_server

The client starts the server over stdio. Each tool is the same function the HTTP interface calls, so an
answer is the same whichever way it is asked, and no model runs here. The store is built from `data/` on
the first call if it does not exist. Nothing here posts anywhere: the tools read and answer.
"""

from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app import claims, view

server = MCPServer(
    "silent-context",
    instructions=(
        "What network experts said in chats and emails, as claims tied to network units, with sources and"
        " validity in time. Ask claims_for before acting on a unit, access_for before driving to a site, and"
        " source to read the thread behind a claim's evidence. A tier of propose means the step may be"
        " proposed; check_first means ask for the check first; unknown means ask the named group."
    ),
)


@server.tool()
def claims_for(
    entity: str,
    symptom: str,
    at: str | None = None,
    link: Literal["up", "down", "unknown"] = "unknown",
    counters: Literal["rising", "zero", "unknown"] = "unknown",
    bounce_done: bool = False,
    bounce_failed: bool = False,
) -> dict[str, Any]:
    """What is known about a unit and a symptom, and what to do next.

    Returns a tier (propose, check_first or unknown), the next step in the expert's own words, the claims
    with their evidence and sources, which group to ask when nothing fits, and the one prohibition: no
    reboot or hardware replacement before a failed bounce is reported. `entity` is a unit id such as
    TRN-051. `at` is a point in world time (ISO 8601); without it, now. `link`, `counters`, `bounce_done`
    and `bounce_failed` are what the caller observed on the unit; counters nobody reports are read from
    telemetry when a recent sample exists.
    """
    observed = {"link": link, "counters": counters, "bounce_done": bounce_done, "bounce_failed": bounce_failed}
    return claims.claims_for(entity, symptom, at, observed)


@server.tool()
def access_for(place: str, at: str | None = None) -> dict[str, Any]:
    """How to reach a place, before anyone drives there, with the age of the information.

    `place` is a site or a node at it. With `at`, what held at that point in world time; if the moment one
    statement replaced another is unknown, both are returned and the answer says so.
    """
    return claims.access_for(place, at)


@server.tool()
def source(file: str) -> dict[str, Any]:
    """One source as it was read, message by message: the thread or email behind a claim's evidence.

    `file` is the source's file name as the evidence names it. Only files in the manifest can be read.
    """
    found = view.source(file)
    if found is None:
        raise ToolError(f"{file}: not a source in the manifest")
    return found


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()

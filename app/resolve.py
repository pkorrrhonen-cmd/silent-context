"""Binds a claim to an entity from what the thread says, using the graph. No model is involved.

An identifier counts only if it is in the graph. Anything unclear waits with its reason, and a
waiting claim is never offered as being about a particular unit.
"""

import json
import re
import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Binding:
    entity: str | None
    reason: str | None


@dataclass(frozen=True)
class Graph:
    nodes: dict[str, dict]
    classes: dict[str, dict]
    site_aliases: dict[str, str]
    site_of_node: dict[str, str]
    barriers_of_site: dict[str, list[str]]
    procedures: dict[str, str]

    @classmethod
    def load(cls, conn: sqlite3.Connection) -> "Graph":
        nodes, classes, aliases, procedures = {}, {}, {}, {}
        for row in conn.execute("SELECT id, kind, name, attrs FROM entity"):
            attrs = json.loads(row["attrs"])
            if row["kind"] == "node":
                nodes[row["id"]] = attrs
            elif row["kind"] == "device_class":
                classes[row["id"]] = attrs
            elif row["kind"] == "procedure_type":
                procedures[row["id"]] = row["name"]
            elif row["kind"] == "site":
                aliases[row["id"].casefold()] = row["id"]
                for alias in attrs.get("aliases", []):
                    aliases[alias.casefold()] = row["id"]
        site_of_node, barriers = {}, {}
        for row in conn.execute("SELECT src, rel, dst FROM edge"):
            if row["rel"] == "LOCATED_AT":
                site_of_node[row["src"]] = row["dst"]
            elif row["rel"] == "HAS_BARRIER":
                barriers.setdefault(row["src"], []).append(row["dst"])
        return cls(nodes, classes, aliases, site_of_node, barriers, procedures)

    def nodes_at(self, site: str) -> set[str]:
        return {node for node, at in self.site_of_node.items() if at == site}

    def nodes_with_port(self, port: str) -> set[str]:
        return {node for node, attrs in self.nodes.items() if port in attrs.get("ports", [])}

    def class_for_version(self, version: str) -> str | None:
        """The one device class a named firmware version points to, if there is exactly one."""
        major = _major(version)
        if major is None:
            return None
        matches = [
            class_id
            for class_id, attrs in self.classes.items()
            if _major(attrs.get("firmware_major", "")) == major
        ]
        return matches[0] if len(matches) == 1 else None


def _major(version: str) -> str | None:
    match = re.search(r"\d+", version)
    return match.group(0) if match else None


def resolve_target(
    graph: Graph,
    kind: str,
    node_ids: list[str],
    sites: list[str],
    ports: list[str],
    firmware: str | None,
    mentions_barrier: bool,
) -> Binding:
    """Each thing the thread names narrows the candidates. They must agree on one entity."""
    named: list[set[str]] = []

    if node_ids:
        wanted = {node.strip().upper() for node in node_ids}
        known = wanted & set(graph.nodes)
        if not known:
            return Binding(None, "unknown_id")
        if len(wanted) > 1:
            return Binding(None, "multiple_candidates")
        named.append(known)

    site_ids: set[str] = set()
    if sites:
        site_ids = {graph.site_aliases.get(site.strip().casefold(), "") for site in sites}
        if "" in site_ids:
            return Binding(None, "unknown_id")
        if len(site_ids) > 1:
            return Binding(None, "multiple_candidates")
        named.append(graph.nodes_at(next(iter(site_ids))))

    for port in ports:
        with_port = graph.nodes_with_port(port.strip())
        if not with_port:
            return Binding(None, "unknown_id")
        named.append(with_port)

    if not named:
        return Binding(None, "no_id")

    candidates = set.intersection(*named)
    if not candidates:
        return Binding(None, "contradicting_context")

    if firmware and _major(firmware) is not None:
        candidates = {
            node
            for node in candidates
            if _major(graph.nodes[node].get("firmware", "")) == _major(firmware)
        }
        if not candidates:
            return Binding(None, "contradicting_context")

    if kind == "access":
        return _bind_access(graph, candidates, site_ids, mentions_barrier)
    if len(candidates) > 1:
        return Binding(None, "multiple_candidates")
    return Binding(next(iter(candidates)), None)


def _bind_access(
    graph: Graph, candidates: set[str], site_ids: set[str], mentions_barrier: bool
) -> Binding:
    """Access knowledge belongs to the place, or to its barrier when the claim is about the barrier."""
    sites = site_ids or {graph.site_of_node[node] for node in candidates if node in graph.site_of_node}
    if len(sites) != 1:
        return Binding(None, "multiple_candidates")
    site = next(iter(sites))
    barriers = graph.barriers_of_site.get(site, [])
    if mentions_barrier and len(barriers) == 1:
        return Binding(barriers[0], None)
    return Binding(site, None)

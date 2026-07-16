"""
DataHubClient is the single gateway PhoenixForge AI's agents use to talk to DataHub.
Every agent imports `datahub_client` from this module and never talks to DataHub
directly -- so all DataHub access flows through one place.

Three modes (set via DEMO_MODE / INTEGRATION_MODE in .env):

  - DEMO_MODE=true (default)
        Reads/writes an in-memory copy of sample_data/mock_datahub_metadata.json.
        Zero setup. This is how judges will run the project most of the time,
        and how `python scripts/run_demo_incident.py` works out of the box.

  - DEMO_MODE=false, INTEGRATION_MODE=mcp (recommended real mode)
        Talks to a real DataHub instance through the official DataHub MCP Server
        (mcp-server-datahub), launched as a subprocess over stdio via mcp_client.py.
        This is the hackathon's primary required integration surface. Both read
        tools (search, get_lineage, list_schema_fields, ...) and write tools
        (add_tags, update_description, save_document, ...) are used -- see the
        write-back methods below.

  - DEMO_MODE=false, INTEGRATION_MODE=graphql (fallback)
        Talks directly to DataHub GMS's GraphQL API. Kept as a documented escape
        hatch for environments where spawning the MCP server subprocess isn't
        possible, but it does NOT by itself satisfy the hackathon's "must use
        MCP Server / Agent Context Kit / DataHub Skills / Analytics Agent"
        requirement -- use "mcp" mode for the submitted entry.

If MCP mode is selected but the MCP server can't be reached (not installed, no
DataHub instance running, etc.), calls fall back to demo data automatically so the
rest of the pipeline keeps working, and a warning is printed once.
"""
import asyncio
import json
import copy
import time
import uuid
import warnings
from typing import Any, Optional

import requests

from .config import settings
from .mcp_client import mcp_datahub_client, MCPUnavailableError


class DataHubClient:
    def __init__(self):
        self.demo_mode = settings.DEMO_MODE
        self.integration_mode = settings.INTEGRATION_MODE
        self._data = None
        self._mcp_warned = False
        # Demo data is always loaded, even in real mode, so a failed MCP/GraphQL
        # call has something sane to fall back to instead of crashing the pipeline.
        self._load_demo_data()

    # ------------------------------------------------------------------ #
    # Demo-mode storage
    # ------------------------------------------------------------------ #
    def _load_demo_data(self):
        with open(settings.SAMPLE_DATA_PATH, "r") as f:
            self._data = json.load(f)

    def _find_dataset(self, urn: str) -> Optional[dict]:
        for ds in self._data["datasets"]:
            if ds["urn"] == urn:
                return ds
        return None

    def _warn_mcp_fallback(self, reason: str):
        if not self._mcp_warned:
            warnings.warn(
                f"[PhoenixForge] DataHub MCP Server unavailable ({reason}). "
                f"Falling back to demo data for this call. Set DEMO_MODE=true to "
                f"silence this, or fix your MCP_SERVER_COMMAND / DataHub connection."
            )
            self._mcp_warned = True

    # ------------------------------------------------------------------ #
    # MCP helper: run an async MCP client call from sync agent code
    # ------------------------------------------------------------------ #
    def _mcp(self, coro_factory):
        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro_factory())
            finally:
                loop.run_until_complete(mcp_datahub_client.close())
                loop.close()
        except MCPUnavailableError as e:
            self._warn_mcp_fallback(str(e))
            return None

    # ------------------------------------------------------------------ #
    # Real DataHub GraphQL helper (fallback path, INTEGRATION_MODE=graphql)
    # ------------------------------------------------------------------ #
    def _graphql(self, query: str, variables: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if settings.DATAHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.DATAHUB_TOKEN}"
        resp = requests.post(
            f"{settings.DATAHUB_GMS_URL}/api/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"DataHub GraphQL error: {body['errors']}")
        return body["data"]

    # ------------------------------------------------------------------ #
    # Public API used by all agents
    # ------------------------------------------------------------------ #
    def get_dataset(self, urn: str) -> dict:
        if self.demo_mode:
            ds = self._find_dataset(urn)
            if not ds:
                raise ValueError(f"Unknown dataset urn in demo data: {urn}")
            return copy.deepcopy(ds)

        if self.integration_mode == "mcp":
            result = self._mcp(lambda: mcp_datahub_client.get_entities([urn]))
            if result is not None:
                return result
            ds = self._find_dataset(urn)
            return copy.deepcopy(ds) if ds else {}

        query = """
        query getDataset($urn: String!) {
          dataset(urn: $urn) {
            urn
            name
            platform { name }
            schemaMetadata { fields { fieldPath type nativeDataType } }
            ownership { owners { owner { ... on CorpUser { username } } } }
            tags { tags { tag { name } } }
            glossaryTerms { terms { term { name } } }
          }
        }
        """
        data = self._graphql(query, {"urn": urn})
        return data["dataset"]

    def search_datasets(self, query_str: str, limit: int = 10) -> list[dict]:
        if self.demo_mode:
            q = query_str.lower()
            return [
                copy.deepcopy(ds)
                for ds in self._data["datasets"]
                if q in ds["name"].lower() or q in ds.get("description", "").lower()
            ][:limit]

        if self.integration_mode == "mcp":
            result = self._mcp(lambda: mcp_datahub_client.search(query_str, limit=limit))
            if result is not None:
                return result
            q = query_str.lower()
            return [copy.deepcopy(ds) for ds in self._data["datasets"] if q in ds["name"].lower()][:limit]

        query = """
        query search($input: SearchInput!) {
          search(input: $input) {
            searchResults { entity { urn ... on Dataset { name } } }
          }
        }
        """
        data = self._graphql(query, {"input": {"type": "DATASET", "query": query_str, "start": 0, "count": limit}})
        return data["search"]["searchResults"]

    def get_lineage(self, urn: str, direction: str = "both") -> dict:
        """Returns {"upstream": [...urns...], "downstream": [...urns...]}"""
        if self.demo_mode:
            edges = self._data["lineage"]
            upstream = [e["source"] for e in edges if e["target"] == urn]
            downstream = [e["target"] for e in edges if e["source"] == urn]
            return {"upstream": upstream, "downstream": downstream}

        if self.integration_mode == "mcp":
            result = self._mcp(lambda: mcp_datahub_client.get_lineage(urn, direction=direction))
            if result is not None:
                return result
            edges = self._data["lineage"]
            return {
                "upstream": [e["source"] for e in edges if e["target"] == urn],
                "downstream": [e["target"] for e in edges if e["source"] == urn],
            }

        query = """
        query lineage($urn: String!, $direction: LineageDirection!) {
          searchAcrossLineage(input: {urn: $urn, direction: $direction, start: 0, count: 100}) {
            searchResults { entity { urn } }
          }
        }
        """
        result = {"upstream": [], "downstream": []}
        for d, key in [("UPSTREAM", "upstream"), ("DOWNSTREAM", "downstream")]:
            data = self._graphql(query, {"urn": urn, "direction": d})
            result[key] = [r["entity"]["urn"] for r in data["searchAcrossLineage"]["searchResults"]]
        return result

    def get_full_lineage_graph(self) -> dict:
        """Returns the whole graph (demo mode only convenience method, used by the dashboard)."""
        if self.demo_mode:
            return {
                "datasets": [
                    {"urn": d["urn"], "name": d["name"], "platform": d["platform"]}
                    for d in self._data["datasets"]
                ],
                "edges": self._data["lineage"],
            }
        raise NotImplementedError("Full graph dump is a demo-mode-only convenience method.")

    def get_ownership(self, urn: str) -> list[str]:
        if self.demo_mode:
            ds = self._find_dataset(urn)
            return ds.get("owners", []) if ds else []
        ds = self.get_dataset(urn)
        owners = ds.get("ownership", {}).get("owners", [])
        return [o["owner"]["username"] for o in owners if "owner" in o]

    def get_assertions(self, urn: str) -> list[dict]:
        if self.demo_mode:
            ds = self._find_dataset(urn)
            return ds.get("assertions", []) if ds else []
        # Real DataHub assertion querying would go through the assertion entity API.
        return []

    def get_recent_changes(self, hours: int = 24) -> list[dict]:
        """Simulated change feed. In demo mode this reads a canned list of recent metadata
        events (schema changes, failed jobs, etc). In real mode this would query DataHub's
        timeline / audit APIs, which is left as an extension point -- polling frequency
        and event volume vary too much by deployment to hardcode here."""
        if self.demo_mode:
            return copy.deepcopy(self._data.get("recent_changes", []))
        return []

    # ------------------------------------------------------------------ #
    # Write-back methods -- this is what makes PhoenixForge AI contribute
    # back into DataHub instead of only reading from it. In MCP mode these
    # call real mutation tools (add_tags, update_description, save_document)
    # exposed by mcp-server-datahub when TOOLS_IS_MUTATION_ENABLED=true.
    # ------------------------------------------------------------------ #
    def write_incident(self, urn: str, incident: dict) -> str:
        incident_urn = f"urn:li:incident:{uuid.uuid4()}"
        record = {
            "urn": incident_urn,
            "dataset_urn": urn,
            "created_at": time.time(),
            **incident,
        }
        if self.demo_mode:
            self._data.setdefault("incident_history", []).append(record)
            return incident_urn

        if self.integration_mode == "mcp":
            title = f"Incident: {incident.get('title', incident_urn)}"
            content = json.dumps(record, indent=2, default=str)
            self._mcp(lambda: mcp_datahub_client.save_document(title=title, content=content))
        return incident_urn

    def write_knowledge_entry(self, entry: dict) -> str:
        entry_urn = f"urn:li:knowledge:{uuid.uuid4()}"
        record = {"urn": entry_urn, "created_at": time.time(), **entry}
        if self.demo_mode:
            self._data.setdefault("knowledge_base", []).append(record)
            return entry_urn

        if self.integration_mode == "mcp":
            title = entry.get("title") or entry.get("incident_title") or f"Runbook {entry_urn}"
            content = entry.get("runbook", json.dumps(record, default=str))
            self._mcp(lambda: mcp_datahub_client.save_document(title=title, content=content))
        return entry_urn

    def search_knowledge(self, query_str: str) -> list[dict]:
        if self.demo_mode:
            q = query_str.lower()
            kb = self._data.get("knowledge_base", [])
            if not query_str:
                return copy.deepcopy(kb)
            return [copy.deepcopy(k) for k in kb if q in json.dumps(k).lower()]
        return []

    def add_tag(self, urn: str, tag: str) -> None:
        if self.demo_mode:
            ds = self._find_dataset(urn)
            if ds is not None:
                ds.setdefault("tags", []).append(tag)
            return
        if self.integration_mode == "mcp":
            self._mcp(lambda: mcp_datahub_client.add_tags(urn, [tag]))

    def suggest_ownership(self, urn: str, owner: str, reason: str) -> None:
        if self.demo_mode:
            ds = self._find_dataset(urn)
            if ds is not None:
                ds.setdefault("suggested_owners", []).append({"owner": owner, "reason": reason})
            return
        if self.integration_mode == "mcp":
            # We suggest rather than assign outright: append the reasoning to the
            # dataset description so a human still confirms the ownership change.
            note = f"\n\n[PhoenixForge AI suggestion] Likely owner: {owner}. Reason: {reason}"
            self._mcp(lambda: mcp_datahub_client.update_description(urn, note))

    def list_incident_history(self) -> list[dict]:
        if self.demo_mode:
            return copy.deepcopy(self._data.get("incident_history", []))
        return []


# Singleton used across the app
datahub_client = DataHubClient()

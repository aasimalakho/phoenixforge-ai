"""
Lineage Intelligence Agent
--------------------------
Traverses the DataHub lineage graph outward from the failing dataset to compute the
"blast radius": every downstream dataset, dashboard, or model that could break as a
result, plus a rough business-risk score based on how many hops away things are and
how many owners/consumers are affected.
"""
import json
from ..datahub_client import datahub_client
from ..llm_client import ask

SYSTEM_PROMPT = """You are the Lineage Intelligence Agent inside PhoenixForge AI. You are
given a blast-radius graph (a failing dataset and everything downstream of it, out to a
few hops). Summarize, in plain English:
1. How many assets are impacted and how severe the overall blast radius is (low/medium/high/critical).
2. Which specific downstream assets matter most (e.g. anything that looks like a dashboard
   or ML model) and why.
3. A one-sentence business-risk statement a non-technical stakeholder could understand.
Be concise - use short bullet points, no more than 150 words total."""


def compute_blast_radius(dataset_urn: str, max_hops: int = 3) -> dict:
    visited = set()
    frontier = [dataset_urn]
    graph_edges = []
    hop = 0

    while frontier and hop < max_hops:
        next_frontier = []
        for urn in frontier:
            if urn in visited:
                continue
            visited.add(urn)
            lineage = datahub_client.get_lineage(urn, direction="downstream")
            for downstream_urn in lineage["downstream"]:
                graph_edges.append({"source": urn, "target": downstream_urn, "hop": hop + 1})
                if downstream_urn not in visited:
                    next_frontier.append(downstream_urn)
        frontier = next_frontier
        hop += 1

    impacted_urns = [v for v in visited if v != dataset_urn]
    impacted_details = [datahub_client.get_dataset(u) for u in impacted_urns]

    upstream = datahub_client.get_lineage(dataset_urn, direction="upstream")["upstream"]

    return {
        "root_urn": dataset_urn,
        "upstream_urns": upstream,
        "impacted_urns": impacted_urns,
        "impacted_details": impacted_details,
        "edges": graph_edges,
        "impacted_count": len(impacted_urns),
    }


def summarize_blast_radius(blast_radius: dict) -> str:
    user_prompt = (
        "Here is the blast radius graph as JSON:\n\n"
        f"{json.dumps(blast_radius, indent=2, default=str)}\n\n"
        "Summarize it per your instructions."
    )
    return ask(SYSTEM_PROMPT, user_prompt, max_tokens=400)

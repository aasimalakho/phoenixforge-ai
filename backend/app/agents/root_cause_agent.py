"""
Root Cause Agent
----------------
Given a detected anomaly, pulls the dataset's schema, ownership, tags, assertions, and
recent change history from DataHub, then asks Claude to reason about what actually
changed, who changed it, and which upstream asset is the true root cause (as opposed to
just the first place the failure was observed).
"""
import json
from ..datahub_client import datahub_client
from ..llm_client import ask

SYSTEM_PROMPT = """You are the Root Cause Agent inside PhoenixForge AI, an autonomous
data-incident investigator built on DataHub metadata. You are precise, evidence-based,
and never speculate beyond the metadata you're given. Given a dataset's current schema,
its upstream lineage, its recent change history, and its data-quality assertions, identify:
1. What actually changed (be specific: field names, types, job names).
2. Who or what changed it, if known from the metadata.
3. Which single upstream asset is the most likely true root cause.
4. Your confidence (low/medium/high) and why.
Respond in concise plain English, structured with short headers. Do not invent metadata
that wasn't provided to you."""


def investigate(dataset_urn: str, upstream_urns: list[str]) -> dict:
    dataset = datahub_client.get_dataset(dataset_urn)
    recent_changes = [
        c for c in datahub_client.get_recent_changes() if c.get("dataset_urn") in [dataset_urn, *upstream_urns]
    ]
    assertions = datahub_client.get_assertions(dataset_urn)
    upstream_details = [datahub_client.get_dataset(u) for u in upstream_urns]

    context = {
        "affected_dataset": dataset,
        "upstream_datasets": upstream_details,
        "recent_changes": recent_changes,
        "assertions": assertions,
    }

    user_prompt = (
        "Here is the DataHub metadata context for this incident, as JSON:\n\n"
        f"{json.dumps(context, indent=2, default=str)}\n\n"
        "Perform your root cause investigation now."
    )

    analysis = ask(SYSTEM_PROMPT, user_prompt, max_tokens=900)

    return {
        "analysis": analysis,
        "context_used": context,
    }

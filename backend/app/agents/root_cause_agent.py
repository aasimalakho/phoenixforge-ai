"""
Root Cause Agent
----------------
Given a detected anomaly, pulls the dataset's schema, ownership, tags, assertions, and
recent change history from DataHub, then asks the LLM to reason about what actually
changed, who changed it, and which upstream asset is the true root cause (as opposed to
just the first place the failure was observed). If the person reported the problem in
their own words, that report is included as primary evidence alongside the metadata.
"""
import json
from ..datahub_client import datahub_client
from ..llm_client import ask

SYSTEM_PROMPT = """You are the Root Cause Agent inside PhoenixForge AI, an autonomous
data-incident investigator built on DataHub metadata. You are precise, evidence-based,
and never speculate beyond the metadata you're given. Given a dataset's current schema,
its upstream lineage, its recent change history, its data-quality assertions, and
(if provided) the reporter's own description of the problem, identify:
1. What actually changed (be specific: field names, types, job names).
2. Who or what changed it, if known from the metadata.
3. Which single upstream asset is the most likely true root cause.
4. Your confidence (low/medium/high) and why.
If a reporter description is provided, treat it as the starting symptom and use the
metadata to confirm or correct it -- don't just repeat it back. Respond in concise plain
English, structured with short headers. Do not invent metadata that wasn't provided to you."""


def investigate(dataset_urn: str, upstream_urns: list[str], user_description: str = None) -> dict:
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

    reported_problem = (
        f"The person reported this problem in their own words:\n\"{user_description}\"\n\n"
        if user_description else ""
    )

    user_prompt = (
        f"{reported_problem}"
        "Here is the DataHub metadata context for this incident, as JSON:\n\n"
        f"{json.dumps(context, indent=2, default=str)}\n\n"
        "Perform your root cause investigation now."
    )

    analysis = ask(SYSTEM_PROMPT, user_prompt, max_tokens=900)

    return {
        "analysis": analysis,
        "context_used": context,
    }

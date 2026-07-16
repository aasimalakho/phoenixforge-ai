"""
Knowledge Agent
---------------
The reason PhoenixForge AI never investigates the same incident twice: after every
repair, this agent distills the whole investigation into a structured knowledge-base
entry and writes it back into DataHub (incident summary, root cause pattern, the repair
that worked, and a runbook-style set of steps). Future incidents on the same or similar
assets can retrieve this instantly instead of starting from zero.
"""
import json
from ..datahub_client import datahub_client
from ..llm_client import ask

SYSTEM_PROMPT = """You are the Knowledge Agent inside PhoenixForge AI. Turn a completed
incident investigation into a short, reusable runbook entry for future agents and
engineers. Format as plain text with these labeled sections:
PATTERN: <short name for this failure pattern, e.g. "upstream schema drift - column rename">
SYMPTOMS: <how this shows up>
ROOT_CAUSE_SUMMARY: <one or two sentences>
FIX_SUMMARY: <one or two sentences>
PREVENTION_TIP: <one sentence>
Keep the whole thing under 120 words."""


def write_knowledge(
    dataset_urn: str,
    incident_title: str,
    root_cause_analysis: str,
    repair_summary: str,
) -> dict:
    user_prompt = (
        f"Incident: {incident_title}\n"
        f"Root cause analysis:\n{root_cause_analysis}\n\n"
        f"Repair summary:\n{repair_summary}\n"
    )
    runbook_text = ask(SYSTEM_PROMPT, user_prompt, max_tokens=350)

    entry = {
        "dataset_urn": dataset_urn,
        "incident_title": incident_title,
        "runbook": runbook_text,
    }
    knowledge_urn = datahub_client.write_knowledge_entry(entry)

    return {"knowledge_urn": knowledge_urn, "runbook": runbook_text}

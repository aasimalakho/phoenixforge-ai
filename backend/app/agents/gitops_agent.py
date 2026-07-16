"""
GitOps Agent
------------
Takes the validated repair and turns it into a real (or dry-run) Pull Request: creates a
branch, commits the fixed file, writes a clear PR description (via Claude) summarizing
the incident, root cause, blast radius, and what was changed, then opens the PR.
"""
from ..github_client import github_client
from ..llm_client import ask

SYSTEM_PROMPT = """You write clear, professional Pull Request descriptions for autonomous
data-pipeline repairs. Given the incident title, root cause analysis, blast radius summary,
and the generated code, write a PR description with these sections:
## Summary
## Root Cause
## Blast Radius
## Fix
## Validation
Keep it under 200 words total. Do not include the full code in the description."""


def open_pull_request(
    incident_title: str,
    dataset_name: str,
    root_cause_analysis: str,
    blast_radius_summary: str,
    validation_result: dict,
    file_path: str,
    code: str,
) -> dict:
    user_prompt = (
        f"Incident: {incident_title}\n"
        f"Dataset: {dataset_name}\n"
        f"Root cause analysis:\n{root_cause_analysis}\n\n"
        f"Blast radius summary:\n{blast_radius_summary}\n\n"
        f"Validation confidence: {validation_result['confidence']}\n"
        f"Validation notes: {validation_result['llm_verdict']}\n"
    )
    pr_body = ask(SYSTEM_PROMPT, user_prompt, max_tokens=500)

    branch_name = "phoenixforge/auto-repair"
    commit_message = f"PhoenixForge AI: autonomous repair for {incident_title}"
    pr_title = f"[PhoenixForge AI] Autonomous repair: {incident_title}"

    pr_url = github_client.open_repair_pr(
        branch_name=branch_name,
        file_path=file_path,
        file_content=code,
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
    )

    return {"pr_url": pr_url, "pr_body": pr_body, "pr_title": pr_title}

"""
Validation Agent
----------------
Before anything gets shipped as a Pull Request, the Validation Agent runs a set of
lightweight, deterministic sanity checks against the generated repair code, then asks
Claude to review it for correctness and estimate a confidence score. This agent is
intentionally conservative: low-confidence repairs are flagged for mandatory human
review rather than auto-merged (see the approval workflow in routes/incidents.py).
"""
import re
from ..llm_client import ask

SYSTEM_PROMPT = """You are the Validation Agent inside PhoenixForge AI. You review a
generated code repair for a data pipeline before it becomes a Pull Request. Check for:
- Obvious syntax problems
- Whether it plausibly addresses the stated root cause
- Any risky patterns (e.g. dropping columns/tables, disabling tests, removing validation)
Respond with a short verdict in this exact format:
CONFIDENCE: <low|medium|high>
RISK_FLAGS: <comma-separated list, or 'none'>
NOTES: <one or two sentences>"""


def run_deterministic_checks(code: str, file_path: str) -> list[str]:
    issues = []
    if not code.strip():
        issues.append("Generated code is empty.")
    if file_path.endswith(".sql") and "select" not in code.lower() and "create" not in code.lower():
        issues.append("SQL file does not appear to contain a SELECT or CREATE statement.")
    if file_path.endswith(".py") and "def " not in code and "@" not in code:
        issues.append("Python file does not appear to define any function/DAG/asset.")
    if re.search(r"\bDROP\s+TABLE\b", code, re.IGNORECASE):
        issues.append("Generated code contains a DROP TABLE statement - flagged for manual review.")
    return issues


def validate_repair(code: str, file_path: str, root_cause_analysis: str) -> dict:
    deterministic_issues = run_deterministic_checks(code, file_path)

    user_prompt = (
        f"Root cause analysis:\n{root_cause_analysis}\n\n"
        f"Generated repair file ({file_path}):\n{code}\n\n"
        f"Deterministic checks already found: {deterministic_issues or 'none'}\n\n"
        "Provide your verdict now."
    )
    verdict_text = ask(SYSTEM_PROMPT, user_prompt, max_tokens=300)

    confidence = "low"
    match = re.search(r"CONFIDENCE:\s*(low|medium|high)", verdict_text, re.IGNORECASE)
    if match:
        confidence = match.group(1).lower()

    requires_human_review = confidence != "high" or len(deterministic_issues) > 0

    return {
        "deterministic_issues": deterministic_issues,
        "llm_verdict": verdict_text,
        "confidence": confidence,
        "requires_human_review": requires_human_review,
    }

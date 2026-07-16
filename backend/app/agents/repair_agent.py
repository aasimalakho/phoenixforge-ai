"""
Repair Agent
------------
Given the root cause analysis, generates an actual code fix: an updated dbt model / SQL
transformation, an Airflow/Dagster/Prefect pipeline patch, or a schema-mapping fix,
depending on what the affected dataset's platform looks like in DataHub metadata.

The generated code is what gets committed and opened as a Pull Request by the GitOps Agent,
and it's also what's saved into examples/ so judges can inspect output quality without
running the whole system.
"""
from ..datahub_client import datahub_client
from ..llm_client import ask

SYSTEM_PROMPT = """You are the Repair Agent inside PhoenixForge AI. You generate production
data-pipeline code fixes. You will be given: the affected dataset's schema, its platform
(e.g. dbt, Airflow, Dagster, Prefect, raw SQL), and a root-cause analysis explaining what
broke. Produce ONE complete, ready-to-commit code file that fixes the issue.

Rules:
- Output ONLY the code file content, no markdown fences, no commentary before or after.
- Add brief inline comments explaining the fix at the specific lines you changed.
- If the platform is dbt, produce a .sql model. If Airflow, a DAG python file. If Dagster,
  an assets.py-style file. If Prefect, a flow python file. If unclear, produce a SQL
  transformation.
- Assume reasonable, idiomatic conventions for that tool."""


def generate_repair(dataset: dict, root_cause_analysis: str) -> dict:
    platform = dataset.get("platform", "sql")
    file_path = _suggest_file_path(dataset, platform)

    user_prompt = (
        f"Affected dataset: {dataset.get('name')}\n"
        f"Platform: {platform}\n"
        f"Schema fields: {dataset.get('schema', [])}\n\n"
        f"Root cause analysis:\n{root_cause_analysis}\n\n"
        "Generate the complete repaired code file now."
    )

    code = ask(SYSTEM_PROMPT, user_prompt, max_tokens=1200)

    return {
        "file_path": file_path,
        "code": code,
        "platform": platform,
    }


def _suggest_file_path(dataset: dict, platform: str) -> str:
    name = dataset.get("name", "unknown_dataset").lower().replace(" ", "_")
    if platform == "dbt":
        return f"models/staging/{name}_fix.sql"
    if platform == "airflow":
        return f"dags/{name}_repair_dag.py"
    if platform == "dagster":
        return f"assets/{name}_repair_asset.py"
    if platform == "prefect":
        return f"flows/{name}_repair_flow.py"
    return f"sql/{name}_repair.sql"

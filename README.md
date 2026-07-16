# PhoenixForge AI

**Self-healing data systems powered by DataHub.**

PhoenixForge AI is an autonomous, multi-agent incident-response platform for data
pipelines. Instead of paging an engineer when a pipeline breaks, it detects the failure,
reasons over DataHub's metadata graph, traces lineage to find the true root cause,
generates a code fix, validates it, opens a Pull Request, and writes what it learned back
into DataHub so no incident is ever investigated twice.

Built for the **DataHub Agent Hackathon** (Agents That Do Real Work / Metadata-Aware Code
Generation & Development challenges).

---

## Why this exists

Traditional observability tools alert you that something broke. PhoenixForge AI acts like
an autonomous data engineer: it investigates, explains, fixes, and remembers.

```
Pipeline Failure Detected
        |
Discovery Agent identifies the failure
        |
Lineage Intelligence Agent computes the blast radius
        |
Root Cause Agent traces it to the true upstream cause
        |
Repair Agent generates the fix (SQL / dbt / Airflow / Dagster / Prefect)
        |
Validation Agent checks it's safe, scores confidence
        |
GitOps Agent opens a Pull Request
        |
Knowledge Agent writes the incident + fix back into DataHub
        |
Future agents retrieve this instantly — no repeated investigation
```

## Agent architecture

| Agent | Responsibility |
|---|---|
| Discovery Agent | Watches DataHub's change feed for schema drift, broken lineage, missing ownership, failed jobs, freshness/quality issues |
| Root Cause Agent | Reasons over schema, lineage, and change history to find what actually broke and why |
| Lineage Intelligence Agent | Traverses the DataHub lineage graph to compute blast radius and business risk |
| Repair Agent | Generates a real, ready-to-commit code fix (dbt/SQL/Airflow/Dagster/Prefect) |
| Validation Agent | Runs deterministic + LLM-reviewed checks, assigns a confidence score, flags anything risky for human review |
| GitOps Agent | Opens a branch, commit, and Pull Request with a clear description |
| Knowledge Agent | Distills the investigation into a runbook and writes it back into DataHub as operational memory |

## DataHub integration

Every agent talks to DataHub through one abstraction, `DataHubClient`
(`backend/app/datahub_client.py`), which in real mode routes through the **official
DataHub MCP Server** (`mcp-server-datahub`) via `backend/app/mcp_client.py` — the
hackathon's required agent-integration surface. The backend launches the MCP server
itself as a subprocess (stdio transport, official `mcp` Python SDK) and calls its real
tools:

- **Read:** `search`, `get_lineage`, `list_schema_fields`, entity/schema lookups —
  used by the Discovery, Lineage Intelligence, and Root Cause agents.
- **Write back:** `add_tags`, `update_description`, `save_document` (enabled via
  `MCP_ENABLE_MUTATIONS=true`) — used by the Knowledge Agent to persist runbooks and by
  the Root Cause Agent to suggest ownership, turning DataHub from a catalog into
  operational memory instead of a read-only lookup.

A direct-GraphQL fallback path (`INTEGRATION_MODE=graphql`) is documented for
environments where running the MCP server isn't possible, but the submitted entry runs
in MCP mode. `DEMO_MODE=true` (the default) reads/writes an in-memory mock graph so the
whole pipeline runs with zero DataHub setup — see `sample_data/mock_datahub_metadata.json`.

We've also drafted a reusable **DataHub Skill** proposal
(`contrib/incident-repair-skill-PROPOSAL.md`) that packages the Root Cause Agent's
lineage-then-runbook-lookup logic as a portable skill definition, disclosed here as a
draft contribution rather than a merged one.

## Demo mode

The whole pipeline runs without any real DataHub instance: `DEMO_MODE=true` (the default)
loads a realistic mock metadata graph from `sample_data/mock_datahub_metadata.json`,
including a pre-built incident scenario (an upstream schema rename that breaks a staging
model, breaches a freshness SLA, and threatens an executive dashboard). Flip
`DEMO_MODE=false` and add real DataHub/GitHub credentials once you have infrastructure to
point at.

## Repository layout

```
backend/          FastAPI app: agents, DataHub MCP client, DB models, routes
frontend/         React + Vite dashboard: incidents, lineage graph, knowledge base, chat
sample_data/      Mock DataHub metadata used in demo mode
examples/         Sample generated repair code, PR description, and runbook
contrib/          Draft DataHub Skill proposal (open-source contribution, bonus criterion)
scripts/          CLI script to run the full pipeline without the UI
.devcontainer/    One-click GitHub Codespaces configuration
```

## Quick start

See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for full plain-English, step-by-step instructions
(written for GitHub Codespaces).

Fastest path:
```bash
# Backend
cd backend
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Or, with zero setup, run the whole agent pipeline from the command line:
```bash
python scripts/run_demo_incident.py
```

## License

Apache License 2.0 — see [LICENSE](./LICENSE).

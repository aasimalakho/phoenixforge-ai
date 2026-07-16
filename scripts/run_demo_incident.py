"""
Run this from backend/ with: python ../scripts/run_demo_incident.py
(or just `python scripts/run_demo_incident.py` from the project root - it adds backend/
to sys.path automatically below)

This triggers the exact scenario baked into sample_data/mock_datahub_metadata.json:
the checkout service silently renamed/rescaled a column, which breaks stg_orders,
which breaches the freshness SLA on fct_daily_revenue, which is what the exec revenue
dashboard reads from.

It runs the full 7-agent pipeline end-to-end and prints every step, so you (or a judge)
can see the whole thing work from the command line with zero UI required.
"""
import os
import sys
import json

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND_DIR)

from app.db.database import init_db, SessionLocal  # noqa: E402
from app.agents import orchestrator  # noqa: E402

TARGET_DATASET = "urn:li:dataset:(urn:li:dataPlatform:dbt,staging.stg_orders,PROD)"


def main():
    init_db()
    db = SessionLocal()

    print("=" * 70)
    print("PhoenixForge AI - Demo Incident Run")
    print("=" * 70)

    incident = orchestrator.create_incident(
        db,
        dataset_urn=TARGET_DATASET,
        title="stg_orders dbt run failing - column 'order_total' missing",
        severity="high",
    )
    print(f"\nCreated incident: {incident.id}")
    print("Running full 7-agent pipeline (this calls the Anthropic API for each agent)...\n")

    result = orchestrator.run_full_investigation(db, incident)

    for trace in result.traces:
        print(f"\n--- Step {trace.step_order}: {trace.agent_name} ---")
        print(trace.summary)

    print("\n" + "=" * 70)
    print(f"Final status: {result.status}")
    print(f"Pull Request: {result.pr_url}")
    print(f"Knowledge base entry: {result.knowledge_urn}")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    main()

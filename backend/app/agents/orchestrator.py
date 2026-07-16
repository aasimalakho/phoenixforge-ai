"""
Orchestrator
------------
Runs the full PhoenixForge AI pipeline for one incident, in order:

  Discovery -> Root Cause -> Lineage Intelligence -> Repair -> Validation
  -> GitOps -> Knowledge

Every step's output is written to the AgentTrace table so the frontend can render an
"agent reasoning trace" timeline, and the Incident row is updated incrementally so you
can watch status change in real time (detected -> investigating -> repaired -> closed).
"""
import json
import time
import uuid
from sqlalchemy.orm import Session

from ..datahub_client import datahub_client
from ..db.models import Incident, AgentTrace
from . import discovery_agent, root_cause_agent, lineage_agent, repair_agent, validation_agent, gitops_agent, knowledge_agent


def _log_step(db: Session, incident_id: str, agent_name: str, order: int, summary: str, detail: str = ""):
    trace = AgentTrace(
        incident_id=incident_id,
        agent_name=agent_name,
        step_order=order,
        summary=summary,
        detail=detail,
        timestamp=time.time(),
    )
    db.add(trace)
    db.commit()

def create_incident(db: Session, dataset_urn: str, title: str, severity: str = "medium", description: str = None) -> Incident:
    incident = Incident(
        id=str(uuid.uuid4()),
        dataset_urn=dataset_urn,
        title=title,
        severity=severity,
        description=description,
        status="detected",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    _log_step(
        db,
        incident.id,
        "Discovery Agent",
        1,
        f"Incident registered for dataset {dataset_urn}.",
        detail=json.dumps({"title": title, "severity": severity}),
    )
    return incident


def run_full_investigation(db: Session, incident: Incident) -> Incident:
    """Runs the entire agent pipeline synchronously and updates the incident row."""
    incident.status = "investigating"
    db.commit()

    dataset = datahub_client.get_dataset(incident.dataset_urn)

    # --- Lineage Intelligence Agent (upstream first, to feed root cause) ---
    blast_radius = lineage_agent.compute_blast_radius(incident.dataset_urn)
    blast_summary = lineage_agent.summarize_blast_radius(blast_radius)
    _log_step(
        db, incident.id, "Lineage Intelligence Agent", 2,
        f"Computed blast radius: {blast_radius['impacted_count']} downstream assets impacted.",
        detail=blast_summary,
    )
    incident.blast_radius_json = json.dumps(blast_radius, default=str)
    db.commit()

    # --- Root Cause Agent ---
    rc_result = root_cause_agent.investigate(incident.dataset_urn, blast_radius["upstream_urns"], user_description=incident.description)
    _log_step(
        db, incident.id, "Root Cause Agent", 3,
        "Completed root cause analysis.",
        detail=rc_result["analysis"],
    )
    incident.root_cause = rc_result["analysis"]
    db.commit()

    # --- Repair Agent ---
    repair = repair_agent.generate_repair(dataset, rc_result["analysis"])
    _log_step(
        db, incident.id, "Repair Agent", 4,
        f"Generated repair for {repair['file_path']} (platform: {repair['platform']}).",
        detail=repair["code"],
    )
    incident.repair_code = repair["code"]
    incident.repair_file_path = repair["file_path"]
    db.commit()

    # --- Validation Agent ---
    validation = validation_agent.validate_repair(repair["code"], repair["file_path"], rc_result["analysis"])
    _log_step(
        db, incident.id, "Validation Agent", 5,
        f"Validation confidence: {validation['confidence']}. Human review required: {validation['requires_human_review']}.",
        detail=validation["llm_verdict"],
    )
    incident.validation_result_json = json.dumps(validation, default=str)
    db.commit()

    # --- GitOps Agent ---
    # High-confidence, no-risk-flag repairs proceed automatically; anything else still
    # opens a PR (nothing merges automatically) but is clearly marked for human review.
    pr_result = gitops_agent.open_pull_request(
        incident_title=incident.title,
        dataset_name=dataset.get("name", incident.dataset_urn),
        root_cause_analysis=rc_result["analysis"],
        blast_radius_summary=blast_summary,
        validation_result=validation,
        file_path=repair["file_path"],
        code=repair["code"],
    )
    _log_step(
        db, incident.id, "GitOps Agent", 6,
        f"Opened Pull Request: {pr_result['pr_url']}",
        detail=pr_result["pr_body"],
    )
    incident.pr_url = pr_result["pr_url"]
    db.commit()

    # --- Knowledge Agent ---
    knowledge = knowledge_agent.write_knowledge(
        dataset_urn=incident.dataset_urn,
        incident_title=incident.title,
        root_cause_analysis=rc_result["analysis"],
        repair_summary=repair["code"][:400],
    )
    _log_step(
        db, incident.id, "Knowledge Agent", 7,
        "Wrote incident knowledge back into DataHub.",
        detail=knowledge["runbook"],
    )
    incident.knowledge_urn = knowledge["knowledge_urn"]

    # write the incident itself back into DataHub as operational memory
    datahub_client.write_incident(
        incident.dataset_urn,
        {
            "title": incident.title,
            "root_cause": incident.root_cause,
            "pr_url": incident.pr_url,
            "confidence": validation["confidence"],
        },
    )

    incident.status = "repaired" if not validation["requires_human_review"] else "awaiting_review"
    incident.updated_at = time.time()
    db.commit()
    db.refresh(incident)
    return incident

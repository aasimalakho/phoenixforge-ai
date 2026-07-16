from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import Incident
from ..models.schemas import TriggerIncidentRequest, IncidentOut
from ..agents import orchestrator, discovery_agent

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/scan")
def scan_for_incidents(db: Session = Depends(get_db)):
    """Runs the Discovery Agent's scan and auto-creates incidents for anything found."""
    candidates = discovery_agent.scan_for_anomalies()
    created = []
    for c in candidates:
        incident = orchestrator.create_incident(db, payload.dataset_urn, payload.title, payload.severity, payload.description)
        created.append(incident.id)
    return {"scanned": len(candidates), "created_incident_ids": created}


@router.post("", response_model=IncidentOut)
def trigger_incident(payload: TriggerIncidentRequest, db: Session = Depends(get_db)):
    """Manually register an incident (used by the dashboard's 'Simulate Incident' button)."""
    incident = orchestrator.create_incident(db, payload.dataset_urn, payload.title, payload.severity, payload.description)
    return incident


@router.post("/{incident_id}/investigate", response_model=IncidentOut)
def investigate_incident(incident_id: str, db: Session = Depends(get_db)):
    """Runs the full 7-agent pipeline against an existing incident."""
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    updated = orchestrator.run_full_investigation(db, incident)
    return updated


@router.get("", response_model=list[IncidentOut])
def list_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).order_by(Incident.created_at.desc()).all()


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

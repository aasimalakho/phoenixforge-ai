import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import Incident
from ..datahub_client import datahub_client
from ..llm_client import ask
from ..models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["dashboard"])

CHAT_SYSTEM_PROMPT = """You are PhoenixForge AI's natural-language interface. Users ask
things like "Why did revenue_dashboard fail?", "Show impacted datasets", "Who owns the
failing asset?", or "What changed in the last 24 hours?". You are given relevant DataHub
metadata and recent incident history as context. Answer directly and concisely in plain
English using only the provided context. If the context doesn't contain the answer, say so
plainly instead of guessing."""


@router.get("/lineage-graph")
def get_lineage_graph():
    """Full graph for the dashboard's interactive lineage visualization."""
    return datahub_client.get_full_lineage_graph()


@router.get("/knowledge")
def search_knowledge(q: str = ""):
    return datahub_client.search_knowledge(q)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(10).all()
    incident_context = [
        {
            "title": i.title,
            "dataset_urn": i.dataset_urn,
            "status": i.status,
            "root_cause": i.root_cause,
            "pr_url": i.pr_url,
        }
        for i in incidents
    ]
    graph = datahub_client.get_full_lineage_graph()

    context = {
        "recent_incidents": incident_context,
        "datasets": graph["datasets"],
        "lineage_edges": graph["edges"],
    }

    user_prompt = (
        f"Context (JSON):\n{json.dumps(context, default=str)}\n\n"
        f"User question: {payload.message}"
    )
    answer = ask(CHAT_SYSTEM_PROMPT, user_prompt, max_tokens=500)
    return ChatResponse(answer=answer)


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    all_incidents = db.query(Incident).all()
    return {
        "total_incidents": len(all_incidents),
        "repaired": len([i for i in all_incidents if i.status == "repaired"]),
        "awaiting_review": len([i for i in all_incidents if i.status == "awaiting_review"]),
        "investigating": len([i for i in all_incidents if i.status == "investigating"]),
        "detected": len([i for i in all_incidents if i.status == "detected"]),
    }

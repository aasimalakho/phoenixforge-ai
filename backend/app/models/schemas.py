from typing import Optional, Any
from pydantic import BaseModel


class TriggerIncidentRequest(BaseModel):
    dataset_urn: str
    title: str
    severity: str = "medium"
    description: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


class AgentTraceOut(BaseModel):
    agent_name: str
    step_order: int
    summary: str
    detail: Optional[str] = None
    timestamp: float

    class Config:
        from_attributes = True


class IncidentOut(BaseModel):
    id: str
    dataset_urn: str
    title: str
    description: Optional[str] = None
    status: str
    severity: str
    created_at: float
    updated_at: float
    root_cause: Optional[str] = None
    blast_radius_json: Optional[str] = None
    repair_code: Optional[str] = None
    repair_file_path: Optional[str] = None
    validation_result_json: Optional[str] = None
    pr_url: Optional[str] = None
    knowledge_urn: Optional[str] = None
    traces: list[AgentTraceOut] = []

    class Config:
        from_attributes = True

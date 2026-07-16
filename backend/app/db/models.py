import time
from sqlalchemy import Column, String, Float, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True)
    dataset_urn = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="detected")  # detected -> investigating -> repaired -> closed
    severity = Column(String, default="medium")
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time)

    root_cause = Column(Text, nullable=True)
    blast_radius_json = Column(Text, nullable=True)   # JSON string
    repair_code = Column(Text, nullable=True)
    repair_file_path = Column(String, nullable=True)
    validation_result_json = Column(Text, nullable=True)
    pr_url = Column(String, nullable=True)
    knowledge_urn = Column(String, nullable=True)

    traces = relationship("AgentTrace", back_populates="incident", cascade="all, delete-orphan")


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String, ForeignKey("incidents.id"))
    agent_name = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(Float, default=time.time)

    incident = relationship("Incident", back_populates="traces")

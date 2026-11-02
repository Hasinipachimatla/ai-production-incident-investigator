from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, DateTime
from app.core.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(
        String(32), 
        default="DETECTED", 
        nullable=False, 
        index=True
    )  # DETECTED, INVESTIGATING, AWAITING_APPROVAL, APPROVED, REJECTED, REMEDIATING, VERIFYING, RESOLVED, RETRYING, FAILED_ESCALATED
    target_system = Column(String(64), default="simulator", nullable=False)
    culprit_service = Column(String(128), nullable=False)
    severity = Column(String(32), default="HIGH")
    symptoms = Column(Text, nullable=False)
    logs_json = Column(Text, default="[]")
    metrics_json = Column(Text, default="{}")
    rca_summary = Column(Text, default="")
    confidence_score = Column(Float, default=0.0)
    confidence_explanation = Column(Text, default="")
    evidence_json = Column(Text, default="[]")
    retrieved_cases_json = Column(Text, default="[]")
    
    proposed_action = Column(String(64), nullable=True)
    action_params_json = Column(Text, default="{}")
    risk_level = Column(String(32), default="LOW")
    
    approved_by = Column(String(128), nullable=True)
    approval_timestamp = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    executed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_status = Column(String(32), nullable=True)  # PASSED, FAILED
    verification_details_json = Column(Text, default="{}")
    
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    resolution_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

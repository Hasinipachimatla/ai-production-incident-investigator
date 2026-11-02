from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class IncidentBase(BaseModel):
    title: str
    culprit_service: str
    severity: str
    symptoms: str

class IncidentCreate(IncidentBase):
    logs: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None

class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: str
    target_system: Optional[str] = "simulator"
    culprit_service: str
    severity: str
    symptoms: str
    rca_summary: Optional[str] = None
    confidence_score: float = 0.0
    confidence_explanation: Optional[str] = None
    proposed_action: Optional[str] = None
    risk_level: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    is_active: bool = False
    created_at: datetime
    updated_at: datetime

class IncidentDetailResponse(IncidentResponse):
    logs: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}
    rca_summary: Optional[str] = None
    evidence: List[Dict[str, Any]] = []
    retrieved_cases: List[Dict[str, Any]] = []
    action_params: Dict[str, Any] = {}
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    executed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verification_status: Optional[str] = None
    verification_details: Dict[str, Any] = {}
    resolution_summary: Optional[str] = None

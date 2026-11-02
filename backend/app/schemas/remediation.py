from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class RemediationActionSpec(BaseModel):
    name: str
    description: str
    risk_level: str
    reversible: bool
    target_service: str
    allowed_parameters: List[str]
    default_parameters: Dict[str, Any]

class RemediationApprovalRequest(BaseModel):
    approved: bool
    approver_name: str
    override_action: Optional[str] = None
    override_params: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None

class RemediationExecuteRequest(BaseModel):
    incident_id: str
    simulate_verification_failure: bool = False

class VerificationResult(BaseModel):
    status: str  # "PASSED" or "FAILED"
    incident_id: str
    culprit_service: str
    pre_metrics: Dict[str, Any]
    post_metrics: Dict[str, Any]
    slo_checks: Dict[str, bool]
    details: str
    should_retry: bool = False
    retry_count: int = 0

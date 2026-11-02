from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class FaultScenarioInfo(BaseModel):
    fault_type: str
    name: str
    target_service: str
    description: str
    reversible: bool
    symptoms: str
    expected_remediation: str

class FaultTriggerRequest(BaseModel):
    fault_type: str
    parameters: Optional[Dict[str, Any]] = None

class FaultStateResponse(BaseModel):
    is_active: bool
    active_faults: List[str]
    current_metrics: Dict[str, Any]
    last_triggered_at: Optional[str] = None

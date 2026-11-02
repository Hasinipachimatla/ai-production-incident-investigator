from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.fault_simulator import fault_simulator
from app.schemas.fault import FaultTriggerRequest, FaultScenarioInfo, FaultStateResponse

router = APIRouter(prefix="/faults", tags=["Fault Simulator"])

@router.get("/catalog", response_model=List[FaultScenarioInfo])
def get_fault_catalog():
    """Returns catalog of reversible controlled failure scenarios."""
    return fault_simulator.get_catalog()

@router.get("/active", response_model=FaultStateResponse)
def get_active_fault_state():
    """Returns current active fault status and live metrics."""
    metrics = fault_simulator.get_current_metrics()
    active_names = fault_simulator.get_active_fault_names()
    return {
        "is_active": len(active_names) > 0,
        "active_faults": active_names,
        "current_metrics": metrics,
        "last_triggered_at": fault_simulator._last_triggered_at
    }

@router.post("/trigger")
def trigger_fault(payload: FaultTriggerRequest):
    """Triggers a controlled reversible failure scenario."""
    try:
        res = fault_simulator.trigger_fault(payload.fault_type, payload.parameters)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset/{fault_type}")
def reset_fault(fault_type: str):
    """Resets a specific active fault scenario back to baseline."""
    return fault_simulator.reset_fault(fault_type)

@router.post("/reset-all")
def reset_all_faults():
    """Resets all active faults, restoring nominal healthy baseline."""
    return fault_simulator.reset_all_faults()

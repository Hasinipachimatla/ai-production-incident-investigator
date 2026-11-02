from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.allowlist import ALLOWLISTED_REMEDIATION_ACTIONS
from app.models.incident import Incident
from app.schemas.remediation import RemediationApprovalRequest, RemediationExecuteRequest
from app.services.remediation_service import remediation_service
from app.api.incident_routes import _to_detail_response

router = APIRouter(prefix="/remediation", tags=["Remediation Control"])

@router.get("/allowlist")
def get_allowlist():
    """Returns all safe allowlisted remediation actions and their parameters."""
    return {
        "allowlisted_actions": list(ALLOWLISTED_REMEDIATION_ACTIONS.values())
    }

@router.post("/approve/{incident_id}")
def approve_remediation(
    incident_id: str,
    payload: RemediationApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Explicit human-in-the-loop approval gate.
    Requires operator name and approval decision.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    try:
        updated_inc = remediation_service.approve_remediation(
            db=db,
            incident=inc,
            approved=payload.approved,
            approver_name=payload.approver_name,
            override_action=payload.override_action,
            override_params=payload.override_params,
            rejection_reason=payload.rejection_reason
        )
        return {
            "status": "success",
            "message": f"Incident {incident_id} is now '{updated_inc.status}'.",
            "incident": _to_detail_response(updated_inc)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/execute/{incident_id}")
def execute_remediation(
    incident_id: str,
    payload: RemediationExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    Executes approved allowlisted fix, collects post-remediation metrics,
    verifies recovery, and closes or retries incident.
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    try:
        result = remediation_service.execute_and_verify(
            db=db,
            incident=inc,
            simulate_verification_failure=payload.simulate_verification_failure
        )
        return {
            "status": "success",
            "incident_status": result["incident"].status,
            "verification": result["verification"],
            "incident": _to_detail_response(result["incident"])
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

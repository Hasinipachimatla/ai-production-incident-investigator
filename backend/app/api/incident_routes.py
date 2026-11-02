import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.incident import Incident
from app.models.audit_log import IncidentAuditLog
from app.schemas.incident import IncidentResponse, IncidentDetailResponse
from app.services.telemetry_service import telemetry_service
from app.services.rca_engine import rca_engine

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    target_system: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    from app.services.monitoring_service import monitoring_service
    active_id = monitoring_service.active_incident_id

    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if service:
        query = query.filter(Incident.culprit_service == service)
    if target_system:
        query = query.filter(Incident.target_system == target_system)
    incidents = query.order_by(Incident.created_at.desc()).all()

    results = []
    for inc in incidents:
        results.append(IncidentResponse(
            id=inc.id,
            title=inc.title,
            status=inc.status,
            target_system=getattr(inc, "target_system", "simulator") or "simulator",
            culprit_service=inc.culprit_service,
            severity=inc.severity,
            symptoms=inc.symptoms,
            rca_summary=inc.rca_summary,
            confidence_score=inc.confidence_score,
            confidence_explanation=getattr(inc, "confidence_explanation", "") or "",
            proposed_action=inc.proposed_action,
            risk_level=inc.risk_level,
            retry_count=inc.retry_count,
            max_retries=inc.max_retries,
            is_active=bool(active_id and inc.id == active_id),
            created_at=inc.created_at,
            updated_at=inc.updated_at
        ))
    return results

@router.get("/active", response_model=Optional[IncidentDetailResponse])
def get_active_incident(
    target_system: Optional[str] = Query("shopease"),
    db: Session = Depends(get_db)
):
    """
    Returns the currently active ongoing incident, if any.
    Returns None if all systems are nominal and healthy.
    """
    from app.services.monitoring_service import monitoring_service
    from app.services.shopease_adapter import shopease_adapter
    from app.services.fault_simulator import fault_simulator

    active_statuses = ["DETECTED", "INVESTIGATING", "AWAITING_APPROVAL", "APPROVED", "REMEDIATING", "VERIFYING", "RETRYING"]

    if target_system == "shopease":
        # 1. Monitoring daemon actively tracks an ongoing sustained anomaly
        if monitoring_service.active_incident_id:
            inc = db.query(Incident).filter(Incident.id == monitoring_service.active_incident_id).first()
            if inc and inc.status in active_statuses:
                return _to_detail_response(inc, is_active=True)

        # 2. Check if live ShopEase telemetry currently reports an active anomaly
        try:
            snapshot = shopease_adapter.collect_snapshot()
            if snapshot.get("anomaly_detected"):
                inc = db.query(Incident).filter(
                    Incident.target_system == "shopease",
                    Incident.status.in_(active_statuses)
                ).order_by(Incident.created_at.desc()).first()
                if inc:
                    return _to_detail_response(inc, is_active=True)
        except Exception:
            pass

        return None
    else:
        # Simulator
        active_faults = fault_simulator.get_active_fault_names()
        if active_faults:
            inc = db.query(Incident).filter(
                Incident.target_system == "simulator",
                Incident.status.in_(active_statuses)
            ).order_by(Incident.created_at.desc()).first()
            if inc:
                return _to_detail_response(inc, is_active=True)
        return None

@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    return _to_detail_response(inc)

from app.services.shopease_adapter import shopease_adapter
from app.services.fault_simulator import fault_simulator

@router.post("/detect-and-investigate")
def detect_and_investigate(
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    preloaded_snapshot: Optional[Dict[str, Any]] = None
):
    """
    Scans operational telemetry, identifies anomalies, runs RCA,
    retrieves historical precedents, prevents duplicate incidents,
    and enters human approval gate.
    """
    # Select telemetry provider based on preloaded snapshot, requested source, or auto-detection
    if preloaded_snapshot:
        target_system = preloaded_snapshot.get("target_system", "shopease" if source == "shopease" else "simulator")
        snapshot = preloaded_snapshot
    elif source == "shopease":
        target_system = "shopease"
        snapshot = shopease_adapter.collect_snapshot()
    elif source == "simulator":
        target_system = "simulator"
        snapshot = telemetry_service.collect_snapshot()
    else:
        # Auto-detect: if simulator has active faults, prioritize simulator for test suite compatibility
        if fault_simulator.get_active_fault_names():
            target_system = "simulator"
            snapshot = telemetry_service.collect_snapshot()
        else:
            # Check live ShopEase system
            try:
                shopease_snapshot = shopease_adapter.collect_snapshot()
                if shopease_snapshot.get("anomaly_detected"):
                    target_system = "shopease"
                    snapshot = shopease_snapshot
                else:
                    target_system = "shopease"
                    snapshot = shopease_snapshot
            except Exception:
                target_system = "simulator"
                snapshot = telemetry_service.collect_snapshot()

    if not snapshot["anomaly_detected"]:
        return {
            "incident_created": False,
            "target_system": target_system,
            "message": "All systems nominal (Error rate < 2%, Latency < 500ms, DB Pool normal, Cache available, Circuit breaker closed). No anomalies detected.",
            "metrics": snapshot["metrics"]
        }

    anomalies = snapshot["anomalies"]
    metrics = snapshot["metrics"]
    logs = snapshot["logs"]

    # Formulate symptoms text
    symptom_descriptions = [f"{a['label']}: current {a['current_value']} breached {a['operator']} {a['threshold']}" for a in anomalies]
    symptoms = "SLO Anomaly Detected: " + "; ".join(symptom_descriptions)

    # Determine primary severity
    severities = [a.get("severity", "WARNING") for a in anomalies]
    primary_sev = "CRITICAL" if "CRITICAL" in severities else "HIGH"

    # Run Evidence-Based RCA (never receives injected fault name)
    rca_res = rca_engine.perform_rca(
        symptoms=symptoms,
        metrics=metrics,
        logs=logs
    )

    culprit_service = rca_res["culprit_service"]

    # Deduplication gate: Avoid creating duplicate incidents for the same ongoing failure within recent window (10 min)
    now_utc = datetime.utcnow()
    active_statuses = ["DETECTED", "INVESTIGATING", "AWAITING_APPROVAL", "APPROVED", "REMEDIATING", "VERIFYING", "RETRYING"]
    existing_incident = db.query(Incident).filter(
        Incident.culprit_service == culprit_service,
        Incident.target_system == target_system,
        Incident.status.in_(active_statuses)
    ).order_by(Incident.created_at.desc()).first()

    if existing_incident:
        age_seconds = (now_utc - existing_incident.created_at).total_seconds() if existing_incident.created_at else 0
        if age_seconds < 600:
            return {
                "incident_created": False,
                "is_duplicate": True,
                "target_system": target_system,
                "message": f"Active ongoing incident [{existing_incident.id}] already tracking {culprit_service} in status '{existing_incident.status}'. Duplicate incident creation prevented.",
                "incident": _to_detail_response(existing_incident)
            }

    inc_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    system_label = "ShopEase" if target_system == "shopease" else "System"
    title = f"{system_label} Incident in {culprit_service}: {anomalies[0]['label']} Degradation"

    incident = Incident(
        id=inc_id,
        title=title,
        status="AWAITING_APPROVAL",  # Enforce Human-in-the-Loop Approval Gate
        target_system=target_system,
        culprit_service=culprit_service,
        severity=primary_sev,
        symptoms=symptoms,
        logs_json=json.dumps(logs),
        metrics_json=json.dumps(metrics),
        rca_summary=rca_res["rca_summary"],
        confidence_score=rca_res["confidence_score"],
        confidence_explanation=rca_res.get("confidence_explanation", ""),
        evidence_json=json.dumps(rca_res["evidence"]),
        retrieved_cases_json=json.dumps(rca_res["retrieved_cases"]),
        proposed_action=rca_res["proposed_action"],
        action_params_json=json.dumps(rca_res["action_params"]),
        risk_level=rca_res["risk_level"],
        retry_count=0,
        max_retries=3,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(incident)
    db.commit()

    # Log audit entry
    audit = IncidentAuditLog(
        incident_id=inc_id,
        stage="DETECTION_AND_RCA",
        action_taken="INCIDENT_CREATED",
        details=f"Detected from operational telemetry ({target_system}). RCA generated with confidence {rca_res['confidence_score']}. Proposed action: {rca_res['proposed_action']}."
    )
    db.add(audit)
    db.commit()
    db.refresh(incident)

    return {
        "incident_created": True,
        "is_duplicate": False,
        "target_system": target_system,
        "incident": _to_detail_response(incident)
    }

def _to_detail_response(inc: Incident, is_active: Optional[bool] = None) -> IncidentDetailResponse:
    from app.services.monitoring_service import monitoring_service
    if is_active is None:
        is_active = bool(monitoring_service.active_incident_id and inc.id == monitoring_service.active_incident_id)

    return IncidentDetailResponse(
        id=inc.id,
        title=inc.title,
        status=inc.status,
        target_system=getattr(inc, "target_system", "simulator") or "simulator",
        culprit_service=inc.culprit_service,
        severity=inc.severity,
        symptoms=inc.symptoms,
        proposed_action=inc.proposed_action,
        risk_level=inc.risk_level,
        confidence_score=inc.confidence_score,
        confidence_explanation=getattr(inc, "confidence_explanation", "") or "",
        retry_count=inc.retry_count,
        max_retries=inc.max_retries,
        is_active=is_active,
        created_at=inc.created_at,
        updated_at=inc.updated_at,
        logs=json.loads(inc.logs_json) if inc.logs_json else [],
        metrics=json.loads(inc.metrics_json) if inc.metrics_json else {},
        rca_summary=inc.rca_summary,
        evidence=json.loads(inc.evidence_json) if inc.evidence_json else [],
        retrieved_cases=json.loads(inc.retrieved_cases_json) if inc.retrieved_cases_json else [],
        action_params=json.loads(inc.action_params_json) if inc.action_params_json else {},
        approved_by=inc.approved_by,
        approval_timestamp=inc.approval_timestamp,
        rejection_reason=inc.rejection_reason,
        executed_at=inc.executed_at,
        verified_at=inc.verified_at,
        verification_status=inc.verification_status,
        verification_details=json.loads(inc.verification_details_json) if inc.verification_details_json else {},
        resolution_summary=inc.resolution_summary
    )

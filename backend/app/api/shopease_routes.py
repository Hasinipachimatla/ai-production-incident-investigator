from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentResponse, IncidentDetailResponse
from app.services.shopease_adapter import shopease_adapter
from app.api.incident_routes import _to_detail_response, detect_and_investigate

router = APIRouter(prefix="/shopease", tags=["ShopEase Integration"])

@router.get("/health")
def get_shopease_health():
    """Checks direct connectivity to ShopEase marketplace and returns health status."""
    return shopease_adapter.check_health()

@router.get("/metrics")
def get_shopease_metrics():
    """Fetches real-time observability metrics from ShopEase."""
    try:
        return {
            "success": True,
            "metrics": shopease_adapter.fetch_metrics()
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch metrics from ShopEase: {str(e)}")

@router.get("/logs")
def get_shopease_logs(limit: int = 100, severity: Optional[str] = None, service: Optional[str] = None):
    """Fetches recent structured JSON logs from ShopEase."""
    try:
        logs = shopease_adapter.fetch_logs(limit=limit, severity=severity, service=service)
        return {
            "success": True,
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch logs from ShopEase: {str(e)}")

@router.get("/services")
def get_shopease_services():
    """Fetches service topology and dependency health from ShopEase."""
    try:
        return {
            "success": True,
            "services": shopease_adapter.fetch_services()
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch services from ShopEase: {str(e)}")

@router.get("/snapshot")
def get_shopease_snapshot():
    """Fetches and returns normalized telemetry snapshot with SLO anomaly detection."""
    try:
        return shopease_adapter.collect_snapshot()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to collect telemetry snapshot from ShopEase: {str(e)}")

@router.get("/faults")
def get_shopease_faults():
    """Fetches active fault scenarios status from ShopEase for verification and demonstration."""
    try:
        return shopease_adapter.fetch_fault_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch fault status from ShopEase: {str(e)}")

@router.post("/faults/inject")
def inject_shopease_fault(payload: Dict[str, Any]):
    """
    Directly inject a controlled fault scenario into ShopEase for demonstration or testing.
    Body: { "scenario": "db_exhaustion" | "high_latency" | "service_error_spike" | "cache_failure" | "circuit_breaker_trip", "params": {} }
    """
    scenario = payload.get("scenario")
    params = payload.get("params", {})
    if not scenario:
        raise HTTPException(status_code=400, detail="Field 'scenario' is required.")

    try:
        with shopease_adapter._client() as client:
            resp = client.post("/api/faults/inject", json={"scenario": scenario, "params": params})
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error injecting fault into ShopEase: {str(e)}")

@router.post("/faults/disable")
def disable_shopease_fault(payload: Dict[str, Any]):
    """Directly disable a fault scenario in ShopEase."""
    scenario = payload.get("scenario")
    if not scenario:
        raise HTTPException(status_code=400, detail="Field 'scenario' is required.")

    try:
        with shopease_adapter._client() as client:
            resp = client.post("/api/faults/disable", json={"scenario": scenario})
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error disabling fault in ShopEase: {str(e)}")

@router.post("/faults/reset")
def reset_all_shopease_faults():
    """Safely reset all fault scenarios in ShopEase to restore healthy baseline."""
    try:
        with shopease_adapter._client() as client:
            resp = client.post("/api/faults/reset")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error resetting ShopEase faults: {str(e)}")

@router.post("/detect-and-investigate")
def detect_and_investigate_shopease(db: Session = Depends(get_db)):
    """Triggers autonomous anomaly detection and RCA specifically on ShopEase evidence."""
    return detect_and_investigate(source="shopease", db=db)

@router.get("/incidents", response_model=List[IncidentResponse])
def list_shopease_incidents(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Lists incidents associated with ShopEase."""
    query = db.query(Incident).filter(Incident.target_system == "shopease")
    if status:
        query = query.filter(Incident.status == status)
    return query.order_by(Incident.created_at.desc()).all()

# ================= BACKGROUND MONITORING CONTROL ENDPOINTS =================

from app.services.monitoring_service import monitoring_service

@router.get("/monitoring/status")
def get_monitoring_status():
    """Returns the operational status of the autonomous background monitoring daemon."""
    return {
        "success": True,
        "monitoring": monitoring_service.get_status()
    }

@router.post("/monitoring/start")
async def start_background_monitoring():
    """Starts or resumes background monitoring against ShopEase."""
    monitoring_service.start()
    return {
        "success": True,
        "message": "Background monitoring daemon started.",
        "monitoring": monitoring_service.get_status()
    }

@router.post("/monitoring/stop")
async def stop_background_monitoring():
    """Pauses or stops the background monitoring daemon."""
    monitoring_service.stop()
    return {
        "success": True,
        "message": "Background monitoring daemon stopped.",
        "monitoring": monitoring_service.get_status()
    }

@router.post("/monitoring/poll-now")
async def force_monitoring_poll():
    """Forces an immediate monitoring cycle against ShopEase."""
    result = await monitoring_service.poll_cycle()
    return {
        "success": True,
        "poll_result": result,
        "monitoring": monitoring_service.get_status()
    }

@router.post("/monitoring/reset")
def reset_monitoring_state(db: Session = Depends(get_db)):
    """Resets daemon streak counters, active incident tracking, and clears stale unapproved incidents to clean nominal baseline."""
    monitoring_service.reset_state()
    from datetime import datetime
    stale_unapproved = db.query(Incident).filter(
        Incident.target_system == "shopease",
        Incident.status.in_(["AWAITING_APPROVAL", "DETECTED"])
    ).all()
    for inc in stale_unapproved:
        inc.status = "RESOLVED"
        inc.resolution_summary = "Closed during monitoring baseline reset."
        inc.updated_at = datetime.utcnow()
    db.commit()
    return {
        "success": True,
        "message": "Monitoring daemon tracking state reset and nominal baseline restored.",
        "closed_stale_count": len(stale_unapproved),
        "monitoring": monitoring_service.get_status()
    }

# ================= REAL CUSTOMER WORKLOAD CONTROLS =================

from app.services.workload_service import workload_service

@router.get("/workload/status")
def get_workload_status():
    """Returns real-time status and telemetry of customer workload generation."""
    return {
        "success": True,
        "workload": workload_service.get_status()
    }

@router.post("/workload/start")
def start_workload_generation(payload: Optional[Dict[str, Any]] = None):
    """
    Starts realistic customer traffic generation against ShopEase.
    Payload: { "concurrency": 35, "ramp_seconds": 6.0, "delay_sec": 0.04 }
    """
    params = payload or {}
    concurrency = int(params.get("concurrency", 35))
    ramp_seconds = float(params.get("ramp_seconds", 6.0))
    delay_sec = float(params.get("delay_sec", 0.04))
    return workload_service.start_workload(
        concurrency=concurrency,
        ramp_seconds=ramp_seconds,
        request_delay_sec=delay_sec
    )

@router.post("/workload/stop")
def stop_workload_generation():
    """Stops customer traffic generation cleanly."""
    return workload_service.stop_workload()

@router.get("/remediation/status")
def get_shopease_remediation_status():
    """Fetches active operational controls status from ShopEase."""
    try:
        with shopease_adapter._client() as client:
            resp = client.get("/api/remediation/status")
            if resp.status_code == 200:
                return resp.json()
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

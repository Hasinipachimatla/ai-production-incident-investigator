from fastapi import APIRouter
from typing import Dict, Any
from app.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.get("/overview")
def get_telemetry_overview():
    """Returns live metrics, recent log stream, and detected anomalies."""
    return telemetry_service.collect_snapshot()

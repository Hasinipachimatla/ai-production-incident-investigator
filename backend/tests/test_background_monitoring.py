import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.services.monitoring_service import BackgroundMonitoringService
from app.models.incident import Incident

@pytest.fixture
def fresh_monitor():
    monitor = BackgroundMonitoringService()
    monitor.consecutive_anomalies_threshold = 2
    return monitor

def test_monitoring_status_nominal(fresh_monitor):
    status = fresh_monitor.get_status()
    assert "target_system" in status
    assert status["target_system"] == "shopease"
    assert status["consecutive_threshold"] == 2
    assert status["polls_count"] == 0
    assert status["is_running"] is False

@pytest.mark.anyio
async def test_monitoring_healthy_poll(fresh_monitor):
    mock_snapshot = {
        "target_system": "shopease",
        "anomaly_detected": False,
        "anomalies": [],
        "metrics": {"error_rate_pct": 0.0, "p99_latency_ms": 25.0}
    }

    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot", return_value=mock_snapshot):
        res = await fresh_monitor.poll_cycle()
        assert res["success"] is True
        assert res["anomaly_detected"] is False
        assert fresh_monitor.consecutive_anomalies == 0
        assert fresh_monitor.consecutive_healthy == 1
        assert fresh_monitor.active_incident_id is None

@pytest.mark.anyio
async def test_monitoring_transient_jitter_does_not_create_incident(fresh_monitor):
    """A single anomaly spike (streak = 1 < threshold 2) should NOT create an incident."""
    mock_anomaly_snapshot = {
        "target_system": "shopease",
        "anomaly_detected": True,
        "anomalies": [{"metric": "error_rate_pct", "label": "API Error Rate", "current_value": 3.5, "threshold": 2.0, "operator": ">"}],
        "metrics": {"error_rate_pct": 3.5, "p99_latency_ms": 45.0},
        "logs": []
    }

    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot", return_value=mock_anomaly_snapshot):
        res = await fresh_monitor.poll_cycle()
        assert res["anomaly_detected"] is True
        assert fresh_monitor.consecutive_anomalies == 1
        # No incident created on first transient glitch
        assert fresh_monitor.active_incident_id is None
        assert fresh_monitor.incidents_created_count == 0

@pytest.mark.anyio
async def test_monitoring_sustained_anomaly_automatically_creates_incident(fresh_monitor, db_session):
    """When anomalies persist across consecutive cycles (streak >= 2), an incident is automatically created."""
    mock_anomaly_snapshot = {
        "target_system": "shopease",
        "timestamp": "2026-11-01T10:00:00.000Z",
        "anomaly_detected": True,
        "anomalies": [{"metric": "db_pool_utilization_pct", "label": "DB Pool Utilization", "current_value": 100.0, "threshold": 80.0, "operator": ">"}],
        "metrics": {"db_pool_utilization_pct": 100.0, "p99_latency_ms": 45.0, "error_rate_pct": 0.0, "circuit_breaker_state": "CLOSED"},
        "logs": [{"service": "checkout-service", "severity": "ERROR", "message": "QueuePool timeout"}]
    }

    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot", return_value=mock_anomaly_snapshot), \
         patch("app.services.monitoring_service.SessionLocal", return_value=db_session):

        # Cycle 1 (Streak = 1)
        await fresh_monitor.poll_cycle()
        assert fresh_monitor.consecutive_anomalies == 1
        assert fresh_monitor.active_incident_id is None

        # Cycle 2 (Streak = 2 >= Threshold 2) -> Trigger automatic incident creation
        await fresh_monitor.poll_cycle()
        assert fresh_monitor.consecutive_anomalies == 2
        assert fresh_monitor.active_incident_id is not None
        assert fresh_monitor.incidents_created_count == 1

        # Check DB record
        created_inc = db_session.query(Incident).filter(Incident.id == fresh_monitor.active_incident_id).first()
        assert created_inc is not None
        assert created_inc.target_system == "shopease"
        assert created_inc.status == "AWAITING_APPROVAL"
        assert created_inc.proposed_action == "restart_connection_pool"

@pytest.mark.anyio
async def test_monitoring_deduplication_prevents_duplicate_incidents(fresh_monitor, db_session):
    """While an ongoing incident is active, subsequent sustained anomaly polls do not create duplicate incidents."""
    mock_anomaly_snapshot = {
        "target_system": "shopease",
        "timestamp": "2026-11-01T10:00:00.000Z",
        "anomaly_detected": True,
        "anomalies": [{"metric": "db_pool_utilization_pct", "label": "DB Pool", "current_value": 100.0, "threshold": 80.0, "operator": ">"}],
        "metrics": {"db_pool_utilization_pct": 100.0, "p99_latency_ms": 45.0, "error_rate_pct": 0.0, "circuit_breaker_state": "CLOSED"},
        "logs": [{"service": "checkout-service", "severity": "ERROR", "message": "QueuePool timeout"}]
    }

    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot", return_value=mock_anomaly_snapshot), \
         patch("app.services.monitoring_service.SessionLocal", return_value=db_session):

        # Consecutive cycle 1 and 2
        await fresh_monitor.poll_cycle()
        await fresh_monitor.poll_cycle()
        first_incident_id = fresh_monitor.active_incident_id
        assert fresh_monitor.incidents_created_count == 1

        # Cycle 3: Still failing, but duplicate must be blocked
        await fresh_monitor.poll_cycle()
        assert fresh_monitor.incidents_created_count == 1
        assert fresh_monitor.active_incident_id == first_incident_id

@pytest.mark.anyio
async def test_monitoring_graceful_recovery_after_connection_error(fresh_monitor):
    """Network connection failure is logged cleanly and recovers on next cycle."""
    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot", side_effect=Exception("Connection refused")):
        res = await fresh_monitor.poll_cycle()
        assert res["success"] is False
        assert fresh_monitor.last_poll_success is False
        assert "Connection refused" in fresh_monitor.last_error

    # Next cycle recovers
    mock_snapshot = {"anomaly_detected": False, "anomalies": [], "metrics": {}}
    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot", return_value=mock_snapshot):
        res2 = await fresh_monitor.poll_cycle()
        assert res2["success"] is True
        assert fresh_monitor.last_poll_success is True
        assert fresh_monitor.last_error is None

def test_monitoring_api_endpoints(client):
    """Verify monitoring control endpoints."""
    # Status
    status_resp = client.get("/api/shopease/monitoring/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["success"] is True
    assert "monitoring" in status_resp.json()

    # Stop & Start
    stop_resp = client.post("/api/shopease/monitoring/stop")
    assert stop_resp.status_code == 200

    start_resp = client.post("/api/shopease/monitoring/start")
    assert start_resp.status_code == 200

    # Poll now
    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot", return_value={"anomaly_detected": False, "anomalies": [], "metrics": {}}):
        poll_resp = client.post("/api/shopease/monitoring/poll-now")
        assert poll_resp.status_code == 200
        assert poll_resp.json()["success"] is True


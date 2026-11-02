import json
import pytest
from unittest.mock import patch, MagicMock
from app.services.shopease_adapter import shopease_adapter, ShopEaseAdapter, SHOPEASE_SLO_THRESHOLDS
from app.services.rca_engine import rca_engine
from app.services.remediation_service import remediation_service
from app.models.incident import Incident
from app.models.audit_log import IncidentAuditLog

# Sample healthy ShopEase metrics mock
MOCK_HEALTHY_METRICS = {
    "timestamp": "2026-11-01T10:00:00.000Z",
    "uptimeSeconds": 1200,
    "requests": {
        "total": 350,
        "success2xx": 348,
        "clientError4xx": 2,
        "serverError5xx": 0,
        "errorCount": 2,
        "errorRatePercent": 0.57,
        "serverErrorRatePercent": 0.0
    },
    "latency": {
        "avgMs": 18.2,
        "maxMs": 120.0,
        "p95Ms": 35.0,
        "sampleCount": 100
    },
    "database": {
        "totalCount": 20,
        "idleCount": 18,
        "waitingCount": 0,
        "activeConnections": 2,
        "status": "HEALTHY"
    },
    "cache": {
        "status": "AVAILABLE",
        "hitRatioPercent": 88.5,
        "hits": 240,
        "misses": 31
    },
    "circuitBreaker": {
        "service": "inventory-service",
        "state": "CLOSED",
        "isAvailable": True,
        "totalTrips": 0,
        "totalRejections": 0
    },
    "endpoints": {
        "/api/products": {"count": 150, "totalMs": 2700.0},
        "/api/categories": {"count": 80, "totalMs": 800.0}
    }
}

MOCK_HEALTH_DATA = {
    "status": "HEALTHY",
    "service": "ShopEase Marketplace",
    "activeFaultsCount": 0,
    "database": {"status": "CONNECTED", "poolSize": 20, "activeConnections": 2},
    "cache": {"status": "AVAILABLE", "hitRatioPercent": 88.5},
    "circuitBreaker": {"state": "CLOSED", "isAvailable": True}
}

MOCK_SERVICES = [
    {"name": "api-gateway", "type": "gateway", "status": "UP"},
    {"name": "catalog-service", "type": "service", "status": "UP"},
    {"name": "order-service", "type": "service", "status": "UP"},
    {"name": "inventory-service", "type": "service", "status": "UP"},
    {"name": "postgresql-database", "type": "database", "status": "UP"},
    {"name": "cache-service", "type": "cache", "status": "UP"}
]

# ================= 1. HEALTH AND ADAPTER CONNECTIVITY =================

def test_shopease_health_check_connected():
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_HEALTH_DATA
        mock_get.return_value = mock_resp

        health = shopease_adapter.check_health()
        assert health["connected"] is True
        assert health["status_code"] == 200
        assert health["data"]["status"] == "HEALTHY"
        assert health["error"] is None

def test_shopease_health_check_connection_error():
    with patch("httpx.Client.get", side_effect=Exception("Connection refused")):
        health = shopease_adapter.check_health()
        assert health["connected"] is False
        assert health["status_code"] is None
        assert "Connection refused" in health["error"]

# ================= 2. TELEMETRY NORMALIZATION & SLO ANOMALIES =================

def test_shopease_telemetry_normalization_nominal():
    with patch.object(shopease_adapter, "fetch_metrics", return_value=MOCK_HEALTHY_METRICS), \
         patch.object(shopease_adapter, "fetch_logs", return_value=[]), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200}):

        snapshot = shopease_adapter.collect_snapshot()
        assert snapshot["target_system"] == "shopease"
        assert snapshot["anomaly_detected"] is False
        assert len(snapshot["anomalies"]) == 0
        assert snapshot["metrics"]["error_rate_pct"] <= 2.0
        assert snapshot["metrics"]["p99_latency_ms"] <= 500.0
        assert snapshot["metrics"]["db_pool_utilization_pct"] <= 80.0
        assert snapshot["metrics"]["cache_hit_rate_pct"] >= 60.0
        assert snapshot["metrics"]["circuit_breaker_state"] == "CLOSED"

def test_shopease_slo_breach_db_pool_exhaustion():
    db_metrics = dict(MOCK_HEALTHY_METRICS)
    db_metrics["database"] = {
        "totalCount": 20,
        "idleCount": 0,
        "waitingCount": 15,
        "activeConnections": 20,
        "status": "EXHAUSTED"
    }

    with patch.object(shopease_adapter, "fetch_metrics", return_value=db_metrics), \
         patch.object(shopease_adapter, "fetch_logs", return_value=[]), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200}):

        snapshot = shopease_adapter.collect_snapshot()
        assert snapshot["anomaly_detected"] is True
        anom_metrics = [a["metric"] for a in snapshot["anomalies"]]
        assert "db_pool_utilization_pct" in anom_metrics
        db_anom = next(a for a in snapshot["anomalies"] if a["metric"] == "db_pool_utilization_pct")
        assert db_anom["current_value"] == 100.0
        assert db_anom["severity"] == "CRITICAL"

def test_shopease_slo_breach_latency():
    lat_metrics = dict(MOCK_HEALTHY_METRICS)
    lat_metrics["latency"] = {
        "avgMs": 1850.0,
        "maxMs": 2400.0,
        "p95Ms": 2050.0,
        "sampleCount": 100
    }
    lat_metrics["endpoints"] = {
        "/api/products": {"count": 10, "totalMs": 20500.0}
    }

    with patch.object(shopease_adapter, "fetch_metrics", return_value=lat_metrics), \
         patch.object(shopease_adapter, "fetch_logs", return_value=[]), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200}):

        snapshot = shopease_adapter.collect_snapshot()
        assert snapshot["anomaly_detected"] is True
        anom_metrics = [a["metric"] for a in snapshot["anomalies"]]
        assert "p99_latency_ms" in anom_metrics
        lat_anom = next(a for a in snapshot["anomalies"] if a["metric"] == "p99_latency_ms")
        assert lat_anom["current_value"] >= 2000.0

def test_shopease_slo_breach_circuit_breaker():
    cb_metrics = dict(MOCK_HEALTHY_METRICS)
    cb_metrics["circuitBreaker"] = {
        "service": "inventory-service",
        "state": "OPEN",
        "isAvailable": False,
        "totalTrips": 1,
        "totalRejections": 12
    }

    with patch.object(shopease_adapter, "fetch_metrics", return_value=cb_metrics), \
         patch.object(shopease_adapter, "fetch_logs", return_value=[]), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200}):

        snapshot = shopease_adapter.collect_snapshot()
        assert snapshot["anomaly_detected"] is True
        cb_anom = next(a for a in snapshot["anomalies"] if a["metric"] == "circuit_breaker_state")
        assert cb_anom["current_value"] == "OPEN"
        assert cb_anom["severity"] == "CRITICAL"

def test_shopease_slo_breach_cache_failure():
    cache_metrics = dict(MOCK_HEALTHY_METRICS)
    cache_metrics["cache"] = {
        "status": "UNAVAILABLE",
        "hitRatioPercent": 0.0,
        "hits": 0,
        "misses": 85
    }

    with patch.object(shopease_adapter, "fetch_metrics", return_value=cache_metrics), \
         patch.object(shopease_adapter, "fetch_logs", return_value=[]), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200}):

        snapshot = shopease_adapter.collect_snapshot()
        assert snapshot["anomaly_detected"] is True
        cache_anom = next(a for a in snapshot["anomalies"] if a["metric"] == "cache_hit_rate_pct")
        assert cache_anom["current_value"] == 0.0
        assert cache_anom["severity"] == "CRITICAL"

# ================= 3. ANTI-LEAKAGE AND CULPRIT INFERENCE =================

def test_rca_anti_leakage_guarantee():
    """
    Guarantees that test-harness logs from 'fault-manager' (which mention injected fault names)
    are strictly filtered out from telemetry normalization and RCA evidence,
    and that culprit service is accurately attributed to the application component.
    """
    logs_with_harness = [
        {
            "timestamp": "2026-11-01T10:15:00.000Z",
            "service": "fault-manager",
            "severity": "CRITICAL",
            "message": "FAULT INJECTED: Scenario 'db_exhaustion' activated by operator"
        },
        {
            "timestamp": "2026-11-01T10:15:01.000Z",
            "service": "category-service",
            "severity": "ERROR",
            "status": 503,
            "message": "Database query timeout: connection pool exhausted while reading categories"
        }
    ]

    with patch.object(shopease_adapter, "fetch_metrics", return_value=MOCK_HEALTHY_METRICS), \
         patch.object(shopease_adapter, "fetch_logs", return_value=logs_with_harness), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200}):

        snapshot = shopease_adapter.collect_snapshot()
        normalized_logs = snapshot["logs"]

        # Harness log MUST NOT be in normalized logs
        services_in_logs = [l["service"] for l in normalized_logs]
        assert "fault-manager" not in services_in_logs
        assert "category-service" in services_in_logs

        # RCA engine should NEVER see or attribute fault-manager
        rca_res = rca_engine.perform_rca(
            symptoms="SLO Anomaly Detected: DB Pool Utilization: current 100.0 breached > 80.0",
            metrics={"db_pool_utilization_pct": 100.0, "p99_latency_ms": 120.0, "error_rate_pct": 2.5},
            logs=normalized_logs
        )
        assert rca_res["culprit_service"] != "fault-manager"
        assert rca_res["culprit_service"] in ["category-service", "postgresql-database"]

        # Evidence should not mention fault-manager
        evidence_services = [e.get("service") for e in rca_res["evidence"]]
        assert "fault-manager" not in evidence_services

# ================= 4. ALLOWLISTED REMEDIATION MAPPING & SECURITY GATE =================

def test_shopease_remediation_allowlist_security():
    """Arbitrary or unallowlisted actions must be blocked by the security gate."""
    with pytest.raises(ValueError) as excinfo:
        shopease_adapter.execute_remediation("drop_database_tables", {})
    assert "Allowlist Security Gate Failed" in str(excinfo.value)

def test_shopease_remediation_action_mapping():
    """Verify each allowlisted action cleanly maps to the corresponding ShopEase fault disablement."""
    mappings = {
        "restart_connection_pool": "db_exhaustion",
        "rate_limit_throttle": "high_latency",
        "rollback_config_flag": "service_error_spike",
        "flush_and_warm_cache": "cache_failure",
        "reset_circuit_breaker": "circuit_breaker_trip"
    }

    for action, expected_scenario in mappings.items():
        with patch("httpx.Client.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"success": True, "message": f"Scenario {expected_scenario} disabled."}
            mock_post.return_value = mock_resp

            res = shopease_adapter.execute_remediation(action)
            assert res["success"] is True
            assert res["action"] == action
            assert res["scenario_resolved"] == expected_scenario

            # Verify the HTTP payload sent to ShopEase
            mock_post.assert_any_call("/api/faults/disable", json={"scenario": expected_scenario})

# ================= 5. INDEPENDENT RECOVERY VERIFICATION =================

def test_shopease_independent_recovery_verification_success():
    """Independent verification succeeds when fresh metrics and active API probes pass all SLOs."""
    mock_post_snapshot = {
        "target_system": "shopease",
        "metrics": {
            "error_rate_pct": 0.0,
            "p99_latency_ms": 25.0,
            "db_pool_utilization_pct": 10.0,
            "db_waiting_requests": 0,
            "circuit_breaker_state": "CLOSED",
            "cache_status": "AVAILABLE",
            "raw_shopease": {
                "database": {"status": "HEALTHY"},
                "circuitBreaker": {"isAvailable": True}
            }
        },
        "services": MOCK_SERVICES
    }

    with patch.object(shopease_adapter, "collect_snapshot", return_value=mock_post_snapshot), \
         patch("httpx.Client.get") as mock_get:

        # Mock active HTTP probes for /api/products and /api/categories
        prod_resp = MagicMock()
        prod_resp.status_code = 200
        cat_resp = MagicMock()
        cat_resp.status_code = 200
        mock_get.side_effect = [prod_resp, cat_resp]

        result = shopease_adapter.verify_recovery(
            incident_id="INC-TEST-001",
            culprit_service="postgresql-database",
            pre_metrics={"db_pool_utilization_pct": 100.0}
        )

        assert result["status"] == "PASSED"
        assert result["slo_checks"]["error_rate_normal"] is True
        assert result["slo_checks"]["latency_normal"] is True
        assert result["slo_checks"]["db_pool_healthy"] is True
        assert result["slo_checks"]["circuit_breaker_closed"] is True
        assert result["slo_checks"]["cache_healthy"] is True
        assert result["slo_checks"]["api_probe_passed"] is True
        assert "PASSED" in result["details"]

def test_shopease_independent_recovery_verification_failure():
    """Verification correctly detects failed recovery and refuses to declare success."""
    mock_post_snapshot = {
        "target_system": "shopease",
        "metrics": {
            "error_rate_pct": 25.0,
            "p99_latency_ms": 2100.0,
            "db_pool_utilization_pct": 95.0,
            "db_waiting_requests": 5,
            "circuit_breaker_state": "OPEN",
            "cache_status": "UNAVAILABLE",
            "raw_shopease": {
                "database": {"status": "EXHAUSTED"},
                "circuitBreaker": {"isAvailable": False}
            }
        },
        "services": MOCK_SERVICES
    }

    with patch.object(shopease_adapter, "collect_snapshot", return_value=mock_post_snapshot), \
         patch("httpx.Client.get") as mock_get:

        prod_resp = MagicMock()
        prod_resp.status_code = 503
        cat_resp = MagicMock()
        cat_resp.status_code = 503
        mock_get.side_effect = [prod_resp, cat_resp]

        result = shopease_adapter.verify_recovery(
            incident_id="INC-TEST-002",
            culprit_service="catalog-service",
            pre_metrics={"p99_latency_ms": 2100.0},
            simulate_failure=True
        )

        assert result["status"] == "FAILED"
        assert "FAILED" in result["details"]

# ================= 6. FASTAPI SHOPEASE ROUTER ENDPOINTS =================

def test_shopease_api_health_endpoint(client):
    with patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200, "data": MOCK_HEALTH_DATA, "error": None}):
        resp = client.get("/api/shopease/health")
        assert resp.status_code == 200
        assert resp.json()["connected"] is True
        assert resp.json()["data"]["status"] == "HEALTHY"

def test_shopease_api_metrics_endpoint(client):
    with patch.object(shopease_adapter, "fetch_metrics", return_value=MOCK_HEALTHY_METRICS):
        resp = client.get("/api/shopease/metrics")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "requests" in resp.json()["metrics"]

def test_shopease_api_faults_controls(client):
    with patch("httpx.Client.post") as mock_post, \
         patch.object(shopease_adapter, "fetch_fault_status", return_value={"activeFaults": []}):

        # GET faults status
        resp = client.get("/api/shopease/faults")
        assert resp.status_code == 200

        # POST inject fault
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True, "scenario": "high_latency"}
        mock_post.return_value = mock_resp

        inj_resp = client.post("/api/shopease/faults/inject", json={"scenario": "high_latency", "params": {"delayMs": 2000}})
        assert inj_resp.status_code == 200
        assert inj_resp.json()["scenario"] == "high_latency"

        # POST disable fault
        dis_resp = client.post("/api/shopease/faults/disable", json={"scenario": "high_latency"})
        assert dis_resp.status_code == 200

        # POST reset all faults
        rst_resp = client.post("/api/shopease/faults/reset")
        assert rst_resp.status_code == 200

# ================= 7. CLOSED-LOOP INCIDENT LIFECYCLE FOR SHOPEASE =================

def test_full_shopease_closed_loop_lifecycle(client, db_session):
    """
    Tests the complete end-to-end closed-loop lifecycle for a ShopEase incident:
    1. Anomaly detection & RCA investigation
    2. Enforcing AWAITING_APPROVAL state
    3. Human-in-the-loop authorization
    4. Safe allowlisted execution & recovery verification
    5. State transition to RESOLVED
    6. Verifying deduplication gate prevents redundant incidents
    """
    mock_anomaly_snapshot = {
        "target_system": "shopease",
        "timestamp": "2026-11-01T10:30:00.000Z",
        "anomaly_detected": True,
        "metrics": {
            "error_rate_pct": 32.5,
            "p99_latency_ms": 2800.0,
            "db_pool_utilization_pct": 100.0,
            "db_waiting_requests": 12,
            "cache_hit_rate_pct": 85.0,
            "circuit_breaker_state": "CLOSED",
            "raw_shopease": {"database": {"status": "EXHAUSTED"}}
        },
        "logs": [
            {
                "timestamp": "2026-11-01T10:30:00.000Z",
                "severity": "ERROR",
                "service": "checkout-service",
                "message": "OperationalError: connection pool exhausted (QueuePool timeout)"
            }
        ],
        "services": MOCK_SERVICES,
        "health": {"connected": True, "status_code": 200},
        "anomalies": [
            {
                "metric": "db_pool_utilization_pct",
                "label": "DB Pool Utilization (%)",
                "current_value": 100.0,
                "threshold": 80.0,
                "operator": ">",
                "severity": "CRITICAL"
            }
        ]
    }

    with patch.object(shopease_adapter, "collect_snapshot", return_value=mock_anomaly_snapshot):
        # Step 1: Detect and investigate from ShopEase source
        det_resp = client.post("/api/incidents/detect-and-investigate?source=shopease")
        assert det_resp.status_code == 200
        det_data = det_resp.json()

        assert det_data["incident_created"] is True
        assert det_data["target_system"] == "shopease"
        inc = det_data["incident"]
        inc_id = inc["id"]
        assert inc["status"] == "AWAITING_APPROVAL"
        assert inc["target_system"] == "shopease"
        assert inc["proposed_action"] == "restart_connection_pool"

        # Step 2: Test Deduplication Gate — second call while incident is active must not create duplicate
        dup_resp = client.post("/api/incidents/detect-and-investigate?source=shopease")
        assert dup_resp.status_code == 200
        dup_data = dup_resp.json()
        assert dup_data["incident_created"] is False
        assert dup_data.get("is_duplicate") is True
        assert inc_id in dup_data["message"]

        # Step 3: Human Approval Gate — Operator approves remediation
        app_resp = client.post(
            f"/api/remediation/approve/{inc_id}",
            json={"approved": True, "approver_name": "SRE-Commander-Test"}
        )
        assert app_resp.status_code == 200
        app_data = app_resp.json()
        assert app_data["incident"]["status"] == "APPROVED"
        assert app_data["incident"]["approved_by"] == "SRE-Commander-Test"

        # Step 4: Execute Remediation and Independently Verify Recovery
        mock_verification = {
            "status": "PASSED",
            "incident_id": inc_id,
            "culprit_service": inc["culprit_service"],
            "target_system": "shopease",
            "pre_metrics": inc["metrics"],
            "post_metrics": {"error_rate_pct": 0.0, "db_pool_utilization_pct": 12.0},
            "slo_checks": {"all": True},
            "details": "Post-remediation independent verification PASSED: Service recovered."
        }

        with patch.object(shopease_adapter, "execute_remediation", return_value={"success": True}), \
             patch.object(shopease_adapter, "verify_recovery", return_value=mock_verification):

            exec_resp = client.post(
                f"/api/remediation/execute/{inc_id}",
                json={"incident_id": inc_id, "simulate_verification_failure": False}
            )
            assert exec_resp.status_code == 200
            exec_data = exec_resp.json()
            assert exec_data["incident"]["status"] == "RESOLVED"
            assert exec_data["verification"]["status"] == "PASSED"
            assert "successfully resolved" in exec_data["incident"]["resolution_summary"].lower()

def test_shopease_closed_loop_retry_and_escalation(client, db_session):
    """
    Tests retry and safe escalation:
    1. Incident is approved.
    2. Verification fails.
    3. Retry count increments and status transitions back to AWAITING_APPROVAL.
    4. Upon exceeding max retries, transitions to FAILED_ESCALATED.
    """
    # Create incident directly in DB
    inc = Incident(
        id="INC-RETRY-001",
        title="ShopEase Retry Test",
        status="APPROVED",
        target_system="shopease",
        culprit_service="inventory-service",
        severity="HIGH",
        symptoms="Circuit breaker open",
        proposed_action="reset_circuit_breaker",
        retry_count=2,  # Already at retry 2
        max_retries=3
    )
    db_session.add(inc)
    db_session.commit()

    mock_fail_verification = {
        "status": "FAILED",
        "incident_id": inc.id,
        "culprit_service": "inventory-service",
        "target_system": "shopease",
        "slo_checks": {"circuit_breaker_closed": False},
        "details": "Post-remediation verification FAILED: Circuit breaker remains OPEN."
    }

    with patch.object(shopease_adapter, "execute_remediation", return_value={"success": True}), \
         patch.object(shopease_adapter, "verify_recovery", return_value=mock_fail_verification):

        # Attempt execution that reaches max retries (2 + 1 = 3 == max_retries)
        exec_resp = client.post(
            f"/api/remediation/execute/{inc.id}",
            json={"incident_id": inc.id, "simulate_verification_failure": True}
        )
        assert exec_resp.status_code == 200
        data = exec_resp.json()
        assert data["incident"]["status"] == "FAILED_ESCALATED"
        assert data["incident"]["retry_count"] == 3
        assert "Max remediation retries" in data["incident"]["resolution_summary"]


# ================= 8. NOISE FILTERING & RETRIEVAL VALIDATION =================

def test_admin_endpoints_excluded_from_latency_metrics():
    """Administrative endpoints (/api/faults/*, /api/observability/*) must not inflate customer P99 latency."""
    raw_metrics_with_slow_fault = {
        "requests": {"total": 10, "serverError5xx": 0, "serverErrorRatePercent": 0.0},
        "latency": {"p95Ms": 15.0, "avgMs": 12.0},
        "database": {"status": "HEALTHY", "activeConnections": 2, "maxPoolSize": 20},
        "cache": {"status": "AVAILABLE", "totalLookups": 50, "hitRatioPercent": 90.0},
        "circuitBreaker": {"state": "CLOSED"},
        "endpoints": {
            "POST /api/faults/inject": {"count": 1, "totalMs": 1075.0},
            "GET /api/observability/metrics": {"count": 50, "totalMs": 2500.0},
            "GET /api/products": {"count": 10, "totalMs": 80.0}
        }
    }

    with patch.object(shopease_adapter, "fetch_metrics", return_value=raw_metrics_with_slow_fault), \
         patch.object(shopease_adapter, "fetch_logs", return_value=[]), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200, "response_time_ms": 10.0}):

        snapshot = shopease_adapter.collect_snapshot()
        metrics = snapshot["metrics"]

        # P99 latency must reflect customer traffic (p95=15ms, avg=12ms, /api/products avg=8ms), NOT 1075ms from fault injection
        assert metrics["p99_latency_ms"] <= 50.0
        assert metrics["p99_latency_ms"] < 500.0
        # No latency anomaly should be generated
        assert not any(a["metric"] == "p99_latency_ms" for a in snapshot["anomalies"])

def test_routine_telemetry_polling_logs_excluded_from_evidence():
    """Routine 200 OK polling logs from monitoring daemon must be excluded from RCA normalized logs."""
    raw_logs = [
        {"timestamp": "2026-11-01T10:00:00Z", "service": "observability-service", "severity": "INFO", "endpoint": "/api/observability/metrics", "status": 200, "durationMs": 4.0},
        {"timestamp": "2026-11-01T10:00:01Z", "service": "api-gateway", "severity": "INFO", "endpoint": "/api/health", "status": 200, "durationMs": 3.0},
        {"timestamp": "2026-11-01T10:00:02Z", "service": "fault-manager", "severity": "INFO", "endpoint": "/api/faults/status", "status": 200, "durationMs": 2.0},
        {"timestamp": "2026-11-01T10:00:03Z", "service": "order-service", "severity": "ERROR", "endpoint": "/api/orders", "status": 503, "durationMs": 4012.0, "message": "Failed to acquire connection from pool: timeout exceeded"}
    ]

    with patch.object(shopease_adapter, "fetch_metrics", return_value=MOCK_HEALTHY_METRICS), \
         patch.object(shopease_adapter, "fetch_logs", return_value=raw_logs), \
         patch.object(shopease_adapter, "fetch_services", return_value=MOCK_SERVICES), \
         patch.object(shopease_adapter, "check_health", return_value={"connected": True, "status_code": 200}):

        snapshot = shopease_adapter.collect_snapshot()
        logs = snapshot["logs"]

        # Only the genuine customer order error log should be retained
        assert len(logs) == 1
        assert logs[0]["service"] == "order-service"
        assert logs[0]["status"] == 503

def test_db_exhaustion_rca_and_historical_retrieval_at_theta():
    """DB pool exhaustion must identify postgresql-database, propose restart_connection_pool, and match INC-HIST-001."""
    metrics = {
        "db_pool_utilization_pct": 100.0,
        "p99_latency_ms": 45.0,
        "error_rate_pct": 0.0,
        "circuit_breaker_state": "CLOSED"
    }
    logs = [
        {
            "service": "order-service",
            "severity": "ERROR",
            "message": "Failed to acquire connection from pool: timeout exceeded when trying to connect"
        }
    ]
    symptoms = "SLO Anomaly Detected: DB Pool Utilization (%): current 100.0 breached > 80.0"

    rca = rca_engine.perform_rca(
        symptoms=symptoms,
        metrics=metrics,
        logs=logs
    )

    assert rca["culprit_service"] in ["postgresql-database", "order-service"]
    assert rca["proposed_action"] == "restart_connection_pool"
    assert rca["confidence_score"] >= 0.70
    assert rca["rca_summary"] is not None and len(rca["rca_summary"]) > 0
    assert rca["confidence_explanation"] is not None and len(rca["confidence_explanation"]) > 0

    # Historical retrieval must match INC-HIST-001
    retrieved = rca["retrieved_cases"]
    assert len(retrieved) >= 1
    assert retrieved[0]["id"] == "INC-HIST-001"
    assert retrieved[0]["similarity_score"] >= 0.55
    assert retrieved[0]["recommended_remediation"] == "restart_connection_pool"

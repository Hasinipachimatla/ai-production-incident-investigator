def test_health_check_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["engine_fitted"] is True

def test_fault_simulator_endpoints(client):
    # Catalog
    cat_res = client.get("/api/faults/catalog")
    assert cat_res.status_code == 200
    assert len(cat_res.json()) >= 5

    # Trigger fault
    trig_res = client.post("/api/faults/trigger", json={"fault_type": "high_latency_cascade"})
    assert trig_res.status_code == 200
    assert trig_res.json()["status"] == "triggered"

    # Check active state
    act_res = client.get("/api/faults/active")
    assert act_res.status_code == 200
    assert "high_latency_cascade" in act_res.json()["active_faults"]

    # Reset all
    reset_res = client.post("/api/faults/reset-all")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "reset_all"

def test_detect_and_investigate_flow(client):
    # Trigger a fault first so telemetry is anomalous
    client.post("/api/faults/trigger", json={"fault_type": "database_connection_exhaustion"})

    # Detect & Investigate
    res = client.post("/api/incidents/detect-and-investigate")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_created"] is True
    inc = data["incident"]
    assert inc["status"] == "AWAITING_APPROVAL"
    assert inc["culprit_service"] == "checkout-service"
    assert inc["proposed_action"] == "restart_connection_pool"
    assert inc["confidence_score"] > 0.70

    inc_id = inc["id"]

    # Approve remediation
    appr_res = client.post(
        f"/api/remediation/approve/{inc_id}",
        json={"approved": True, "approver_name": "Test-Commander"}
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["incident"]["status"] == "APPROVED"

    # Execute remediation
    exec_res = client.post(
        f"/api/remediation/execute/{inc_id}",
        json={"incident_id": inc_id, "simulate_verification_failure": False}
    )
    assert exec_res.status_code == 200
    assert exec_res.json()["incident_status"] == "RESOLVED"
    assert exec_res.json()["verification"]["status"] == "PASSED"

def test_retrieval_comparison_endpoint(client):
    payload = {
        "query_text": "PostgreSQL connection pool exhausted in checkout flow",
        "service": "checkout-service",
        "top_k": 3,
        "threshold": 0.55,
        "ground_truth_case_ids": ["INC-HIST-001"]
    }
    res = client.post("/api/retrieval/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "fixed_top_k" in data
    assert "adaptive" in data
    assert data["fixed_top_k"]["retrieved_count"] == 3
    assert data["adaptive"]["retrieved_count"] <= 2
    assert "analysis" in data

def test_experiment_run_endpoint(client):
    res = client.post("/api/experiments/run", json={"threshold": 0.55, "top_k": 3})
    assert res.status_code == 200
    report = res.json()
    assert "baseline_top_k" in report
    assert "adaptive_threshold" in report
    assert report["num_queries"] >= 10
    assert report["baseline_top_k"]["total_retrieved"] == report["num_queries"] * 3
    assert report["adaptive_threshold"]["total_irrelevant"] <= report["baseline_top_k"]["total_irrelevant"]

def test_full_e2e_remediation_lifecycle(client):
    """
    Complete integration test through REST API:
    1. Reset system to healthy baseline.
    2. Trigger cache storm fault.
    3. Detect anomaly & investigate via API.
    4. Validate RCA details, evidence, and safety rationale.
    5. Approve remediation via API.
    6. Execute remediation via API.
    7. Verify incident status is RESOLVED and telemetry restored.
    """
    # 1. Reset
    client.post("/api/faults/reset-all")

    # 2. Trigger cache storm
    trig_res = client.post("/api/faults/trigger", json={"fault_type": "cache_invalidation_storm"})
    assert trig_res.status_code == 200

    # 3. Detect and investigate
    det_res = client.post("/api/incidents/detect-and-investigate")
    assert det_res.status_code == 200
    det_data = det_res.json()
    assert det_data["incident_created"] is True
    inc = det_data["incident"]
    assert inc["status"] == "AWAITING_APPROVAL"
    assert inc["culprit_service"] == "catalog-service"
    assert inc["proposed_action"] == "flush_and_warm_cache"
    assert len(inc["evidence"]) > 0

    inc_id = inc["id"]

    # 4. Human Approval
    appr_res = client.post(
        f"/api/remediation/approve/{inc_id}",
        json={"approved": True, "approver_name": "Senior-SRE-Dan"}
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["incident"]["status"] == "APPROVED"

    # 5. Execution & Verification
    exec_res = client.post(
        f"/api/remediation/execute/{inc_id}",
        json={"incident_id": inc_id, "simulate_verification_failure": False}
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["incident_status"] == "RESOLVED"
    assert exec_data["verification"]["status"] == "PASSED"

    # 6. Verify Incident List shows resolved
    list_res = client.get("/api/incidents")
    assert list_res.status_code == 200
    resolved_ids = [item["id"] for item in list_res.json() if item["status"] == "RESOLVED"]
    assert inc_id in resolved_ids

def test_csv_and_json_experiment_outputs(client):
    """Verify experiment run generates both JSON and CSV output files."""
    from app.core.config import settings

    res = client.post("/api/experiments/run", json={"threshold": 0.55, "top_k": 3})
    assert res.status_code == 200

    json_path = settings.DATA_DIR / "last_experiment_results.json"
    csv_path = settings.DATA_DIR / "last_experiment_results.csv"

    assert json_path.exists()
    assert csv_path.exists()
    assert csv_path.stat().st_size > 500

def test_active_incident_endpoint_nominal_with_historical_unapproved_incident(client, db_session):
    """
    Regression Test:
    When ShopEase is healthy and nominal, GET /api/incidents/active must return null (None),
    even if historical incidents in status AWAITING_APPROVAL exist in the database.
    This guarantees that unapproved past records (like phantom incidents) are never displayed
    as live ongoing emergency banners.
    """
    from unittest.mock import patch
    from app.models.incident import Incident
    from app.services.monitoring_service import monitoring_service

    # Ensure monitoring daemon has no active incident
    monitoring_service.active_incident_id = None

    # Insert a historical incident with status AWAITING_APPROVAL
    hist_inc = Incident(
        id="INC-HIST-AWAITING-001",
        title="Historical Unapproved Incident",
        status="AWAITING_APPROVAL",
        target_system="shopease",
        culprit_service="catalog-service",
        severity="HIGH",
        symptoms="Catalog latency spike",
        rca_summary="Precedent match",
        confidence_score=0.72,
        proposed_action="rate_limit_throttle",
        risk_level="LOW",
        retry_count=0,
        max_retries=3,
        logs_json="[]",
        metrics_json="{}",
        evidence_json="[]",
        retrieved_cases_json="[]",
        action_params_json="{}"
    )
    db_session.add(hist_inc)
    db_session.commit()

    # Mock ShopEase snapshot as nominal (anomaly_detected=False)
    with patch("app.services.shopease_adapter.shopease_adapter.collect_snapshot") as mock_snap:
        mock_snap.return_value = {
            "connected": True,
            "anomaly_detected": False,
            "activeFaults": [],
            "metrics": {"error_rate_pct": 0.0, "p99_latency_ms": 15.0}
        }
        res = client.get("/api/incidents/active?target_system=shopease")
        assert res.status_code == 200
        assert res.json() is None

        # Verify /api/incidents lists it with is_active=False
        list_res = client.get("/api/incidents?target_system=shopease")
        assert list_res.status_code == 200
        items = list_res.json()
        matching = [i for i in items if i["id"] == "INC-HIST-AWAITING-001"]
        assert len(matching) == 1
        assert matching[0]["is_active"] is False

def test_active_incident_endpoint_when_monitoring_daemon_tracks_active_incident(client, db_session):
    """
    Regression Test:
    When the autonomous monitoring daemon is actively tracking an incident ID,
    GET /api/incidents/active returns that incident with is_active=True.
    """
    from app.models.incident import Incident
    from app.services.monitoring_service import monitoring_service

    active_inc = Incident(
        id="INC-LIVE-TEST-002",
        title="Live PostgreSQL Pool Exhaustion",
        status="AWAITING_APPROVAL",
        target_system="shopease",
        culprit_service="postgresql-database",
        severity="CRITICAL",
        symptoms="Pool at 100%",
        rca_summary="Database connection pool exhaustion",
        confidence_score=0.95,
        proposed_action="restart_connection_pool",
        risk_level="LOW",
        retry_count=0,
        max_retries=3,
        logs_json="[]",
        metrics_json="{}",
        evidence_json="[]",
        retrieved_cases_json="[]",
        action_params_json="{}"
    )
    db_session.add(active_inc)
    db_session.commit()

    monitoring_service.active_incident_id = active_inc.id
    try:
        res = client.get("/api/incidents/active?target_system=shopease")
        assert res.status_code == 200
        data = res.json()
        assert data is not None
        assert data["id"] == "INC-LIVE-TEST-002"
        assert data["is_active"] is True
        assert data["culprit_service"] == "postgresql-database"

        # Verify /api/incidents marks it is_active=True
        list_res = client.get("/api/incidents?target_system=shopease")
        assert list_res.status_code == 200
        matching = [i for i in list_res.json() if i["id"] == "INC-LIVE-TEST-002"]
        assert len(matching) == 1
        assert matching[0]["is_active"] is True
    finally:
        monitoring_service.active_incident_id = None

def test_active_incident_endpoint_simulator_active_fault(client):
    """
    Regression Test:
    Verify that Simulator mode correctly reports active incident during faults,
    and returns null when all simulator faults are reset.
    """
    # 1. Nominal baseline
    client.post("/api/faults/reset-all")
    res_nominal = client.get("/api/incidents/active?target_system=simulator")
    assert res_nominal.status_code == 200
    assert res_nominal.json() is None

    # 2. Trigger fault and detect
    client.post("/api/faults/trigger", json={"fault_type": "high_latency_cascade"})
    det_res = client.post("/api/incidents/detect-and-investigate?source=simulator")
    assert det_res.status_code == 200
    created_id = det_res.json()["incident"]["id"]

    # 3. GET /api/incidents/active should now return the active incident
    act_res = client.get("/api/incidents/active?target_system=simulator")
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data is not None
    assert act_data["id"] == created_id
    assert act_data["is_active"] is True

    # 4. Reset faults
    client.post("/api/faults/reset-all")
    res_after_reset = client.get("/api/incidents/active?target_system=simulator")
    assert res_after_reset.status_code == 200
    assert res_after_reset.json() is None



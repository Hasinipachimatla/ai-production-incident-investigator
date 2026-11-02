"""
Live End-to-End Validation Script: ShopEase + AI Incident Investigator
Executes the rigorous 15-step closed-loop lifecycle across all 5 fault scenarios against the running ShopEase server (http://localhost:5000).
"""

import sys
import json
import time
from pathlib import Path

# Configure utf-8 encoding for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import SessionLocal, ensure_migrations
from app.services.shopease_adapter import shopease_adapter
from app.services.rca_engine import rca_engine
from app.services.remediation_service import remediation_service
from app.models.incident import Incident
from app.models.audit_log import IncidentAuditLog
from app.services.retrieval_engine import retrieval_engine

SCENARIOS = [
    {
        "name": "Scenario 1: Database Connection Pool Exhaustion",
        "scenario": "db_exhaustion",
        "params": {"safetyTimeoutSeconds": 60},
        "trigger_url": "/api/categories?nocache=true",
        "expected_anomaly_metric": "db_pool_utilization_pct",
        "expected_action": "restart_connection_pool",
        "expected_culprit": ["postgresql-database", "checkout-service", "category-service"]
    },
    {
        "name": "Scenario 2: High API Latency Cascade",
        "scenario": "high_latency",
        "params": {"delayMs": 2000},
        "trigger_url": "/api/products?search=kurti",
        "expected_anomaly_metric": "p99_latency_ms",
        "expected_action": "rate_limit_throttle",
        "expected_culprit": ["catalog-service", "api-gateway"]
    },
    {
        "name": "Scenario 3: Checkout Service 500 Error Spike",
        "scenario": "service_error_spike",
        "params": {},
        "trigger_url": "/api/orders",
        "trigger_method": "POST",
        "trigger_body": {
            "customer_name": "Priya Sharma",
            "customer_phone": "9876543210",
            "shipping_address": "Indiranagar",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560038",
            "payment_method": "Cash on Delivery",
            "items": [{"product_id": 1, "name": "Chanderi Silk Anarkali Kurti", "price": 1499, "quantity": 1}]
        },
        "expected_anomaly_metric": "error_rate_pct",
        "expected_action": "rollback_config_flag",
        "expected_culprit": ["order-service", "checkout-service"]
    },
    {
        "name": "Scenario 4: Cache Invalidation Storm & Outage",
        "scenario": "cache_failure",
        "params": {},
        "trigger_url": "/api/categories",
        "expected_anomaly_metric": "cache_hit_rate_pct",
        "expected_action": "flush_and_warm_cache",
        "expected_culprit": ["cache-service", "catalog-service"]
    },
    {
        "name": "Scenario 5: Downstream Circuit Breaker Trip (Inventory)",
        "scenario": "circuit_breaker_trip",
        "params": {"failRequests": 4},
        "trigger_url": "/api/inventory/check?productId=1&quantity=2",
        "expected_anomaly_metric": "circuit_breaker_state",
        "expected_action": "reset_circuit_breaker",
        "expected_culprit": ["inventory-service"]
    }
]

def main():
    print("=" * 70)
    print("🔬 ShopEase + AI Incident Investigator — Live Closed-Loop Validation")
    print(f"Target Base URL: {shopease_adapter.base_url}")
    print("=" * 70)

    # 1. Check ShopEase Connectivity
    health = shopease_adapter.check_health()
    if not health.get("connected"):
        print(f"❌ ERROR: Cannot connect to ShopEase at {shopease_adapter.base_url}: {health.get('error')}")
        sys.exit(1)
    print(f"✅ ShopEase Connectivity Verified: HTTP {health.get('status_code')} (latency: {health.get('response_time_ms')}ms)")

    # 2. Reset All Faults to clean baseline
    with shopease_adapter._client() as client:
        client.post("/api/faults/reset")
    time.sleep(1)
    print("✅ System Baseline Reset to Nominal Health.")

    # 3. Ensure Historical Cases are Loaded in Vector Index
    if settings.HISTORICAL_INCIDENTS_PATH.exists():
        with open(settings.HISTORICAL_INCIDENTS_PATH, "r", encoding="utf-8") as f:
            cases = json.load(f)
            retrieval_engine.load_cases(cases)
        print(f"✅ Loaded {len(cases)} Historical Cases into Adaptive Retrieval Engine.")

    db = SessionLocal()
    ensure_migrations()

    passed_scenarios = 0
    total_scenarios = len(SCENARIOS)

    try:
        for idx, sc in enumerate(SCENARIOS, 1):
            print("\n" + "-" * 70)
            print(f"▶ [{idx}/{total_scenarios}] Validating: {sc['name']}")
            print("-" * 70)

            # Step 1 & 2: Verify Baseline & Inject Fault
            print(f"  • Injecting fault '{sc['scenario']}' into ShopEase...")
            with shopease_adapter._client() as client:
                inj_resp = client.post("/api/faults/inject", json={"scenario": sc["scenario"], "params": sc["params"]})
                assert inj_resp.status_code == 200, f"Injection failed: {inj_resp.text}"

            # Step 3: Trigger Endpoint to generate operational symptoms
            print(f"  • Triggering target endpoint: {sc['trigger_url']} ...")
            try:
                with shopease_adapter._client() as client:
                    if sc.get("trigger_method") == "POST":
                        client.post(sc["trigger_url"], json=sc.get("trigger_body", {}))
                    else:
                        client.get(sc["trigger_url"])
            except Exception as e:
                # Deliberate failures (like timeout or 503) are expected symptoms
                pass

            time.sleep(1.0)

            # Step 4: Collect Telemetry & Anomaly Detection
            print("  • Collecting live normalized telemetry & scanning SLO thresholds...")
            snapshot = shopease_adapter.collect_snapshot()
            assert snapshot["anomaly_detected"] is True, f"Expected anomaly detected for {sc['scenario']}"

            detected_metrics = [a["metric"] for a in snapshot["anomalies"]]
            print(f"    - Breached Metrics: {detected_metrics}")
            assert sc["expected_anomaly_metric"] in detected_metrics, f"Expected {sc['expected_anomaly_metric']} in {detected_metrics}"

            # Step 5: Evidence-Based RCA (with strict anti-leakage guarantee)
            print("  • Running evidence-based RCA (anti-leakage guarantee verified)...")
            symptoms = "SLO Anomaly Detected: " + "; ".join([f"{a['label']} breached {a['operator']} {a['threshold']}" for a in snapshot["anomalies"]])
            rca_res = rca_engine.perform_rca(
                symptoms=symptoms,
                metrics=snapshot["metrics"],
                logs=snapshot["logs"]
            )

            # Anti-leakage checks
            assert rca_res["culprit_service"] != "fault-manager", "Anti-leakage breach: culprit assigned to test harness!"
            for e in rca_res["evidence"]:
                assert e.get("service") != "fault-manager", "Anti-leakage breach: test harness log exposed in evidence!"

            print(f"    - Culprit Service: {rca_res['culprit_service']}")
            print(f"    - Confidence Score: {rca_res['confidence_score'] * 100:.1f}%")
            print(f"    - Proposed Action: {rca_res['proposed_action']}")
            print(f"    - Retrieved Precedents: {len(rca_res['retrieved_cases'])} matches")

            assert rca_res["proposed_action"] == sc["expected_action"], f"Expected action {sc['expected_action']}, got {rca_res['proposed_action']}"

            # Step 6: Create Incident Record in DB
            inc_id = f"INC-LIVE-{sc['scenario'].upper()}-{int(time.time())}"
            incident = Incident(
                id=inc_id,
                title=f"ShopEase Live Incident: {sc['name']}",
                status="AWAITING_APPROVAL",
                target_system="shopease",
                culprit_service=rca_res["culprit_service"],
                severity="HIGH",
                symptoms=symptoms,
                logs_json=json.dumps(snapshot["logs"]),
                metrics_json=json.dumps(snapshot["metrics"]),
                rca_summary=rca_res["rca_summary"],
                confidence_score=rca_res["confidence_score"],
                evidence_json=json.dumps(rca_res["evidence"]),
                retrieved_cases_json=json.dumps(rca_res["retrieved_cases"]),
                proposed_action=rca_res["proposed_action"],
                action_params_json=json.dumps(rca_res["action_params"]),
                risk_level=rca_res["risk_level"]
            )
            db.add(incident)
            db.commit()
            print(f"  • Incident record [{inc_id}] created. Status: {incident.status}")

            # Step 7: Human Approval Gate
            print("  • Human-in-the-Loop Approval Gate: Authorizing allowlisted mitigation...")
            remediation_service.approve_remediation(
                db=db,
                incident=incident,
                approved=True,
                approver_name="Faculty-Reviewer-Live"
            )
            assert incident.status == "APPROVED"
            print(f"    - Status: {incident.status} (Approved by {incident.approved_by})")

            # Step 8: Closed-Loop Execution & Multi-SLO Recovery Verification
            print(f"  • Executing mitigation '{incident.proposed_action}' and independently verifying recovery...")
            exec_res = remediation_service.execute_and_verify(db=db, incident=incident)
            verification = exec_res["verification"]

            print(f"    - Verification Status: {verification['status']}")
            print(f"    - Incident Final Status: {incident.status}")
            assert verification["status"] == "PASSED", f"Verification failed: {verification.get('details')}"
            assert incident.status == "RESOLVED"
            print(f"  ✅ {sc['name']} SUCCESSFULLY RESOLVED & VERIFIED!")
            passed_scenarios += 1

            # Reset between scenarios
            with shopease_adapter._client() as client:
                client.post("/api/faults/reset")
            time.sleep(1.0)

        # 4. Verify Failure Retry & Escalation Loop
        print("\n" + "-" * 70)
        print("▶ Validating Retry & Escalation Safeguard on Verification Failure")
        print("-" * 70)

        esc_id = f"INC-LIVE-ESCALATE-{int(time.time())}"
        esc_inc = Incident(
            id=esc_id,
            title="ShopEase Escalation Loop Test",
            status="AWAITING_APPROVAL",
            target_system="shopease",
            culprit_service="inventory-service",
            severity="CRITICAL",
            symptoms="Synthesized verification failure test",
            proposed_action="reset_circuit_breaker",
            action_params_json="{}",
            retry_count=2,  # Already 2 prior attempts
            max_retries=3
        )
        db.add(esc_inc)
        db.commit()

        # Approve attempt 3
        remediation_service.approve_remediation(db, esc_inc, approved=True, approver_name="Commander-Escalation")

        # Force verification failure to test escalation safeguard
        fail_res = remediation_service.execute_and_verify(db, esc_inc, simulate_verification_failure=True)
        assert esc_inc.status == "FAILED_ESCALATED", f"Expected FAILED_ESCALATED, got {esc_inc.status}"
        assert esc_inc.retry_count == 3
        print(f"  ✅ Safely escalated to human incident commander after {esc_inc.retry_count} retries.")
        print(f"    - Final State: {esc_inc.status}")
        print(f"    - Resolution Summary: {esc_inc.resolution_summary}")

    finally:
        db.close()
        # Final cleanup: ensure ShopEase is restored to healthy baseline
        with shopease_adapter._client() as client:
            client.post("/api/faults/reset")

    print("\n" + "=" * 70)
    print(f"🏆 ALL {passed_scenarios}/{total_scenarios} LIVE FAULT SCENARIOS + ESCALATION VALIDATED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    main()

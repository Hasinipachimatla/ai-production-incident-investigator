#!/usr/bin/env python3
"""
test_live_automatic_monitoring.py
=================================
Validates the fully autonomous closed-loop operation between ShopEase (:5000)
and AI Production Incident Investigator (:8000).

Scenario:
1. Baseline health verification (both systems online and nominal).
2. Inject fault directly into ShopEase (simulating a real production failure).
3. Wait for background monitoring daemon to detect sustained anomaly (>=2 polls).
4. Verify incident was automatically created in SQLite and entered AWAITING_APPROVAL.
5. Authorize remediation (Human-in-the-Loop approval gate).
6. Execute allowlisted remediation and verify multi-SLO recovery.
7. Verify incident status transitions to RESOLVED and system returns to nominal.
"""

import sys
import io
import time
import json
import urllib.request
import urllib.error

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SHOPEASE_URL = "http://localhost:5000"
INVESTIGATOR_URL = "http://127.0.0.1:8000"

def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "AutonomousMonitorTest/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_post(url, data=None):
    payload = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "AutonomousMonitorTest/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 80)
    print("  LIVE AUTONOMOUS BACKGROUND MONITORING & CLOSED-LOOP VALIDATION")
    print("=" * 80)

    # 1. Check services
    print("\n[Step 1] Checking ShopEase (:5000) and Investigator (:8000) health...")
    try:
        shopease_h = http_get(f"{SHOPEASE_URL}/api/health")
        print(f"  [PASS] ShopEase Status: {shopease_h.get('status')}")
    except Exception as e:
        print(f"  [FAIL] ShopEase offline: {e}")
        return 1

    try:
        investigator_h = http_get(f"{INVESTIGATOR_URL}/api/health")
        print(f"  [PASS] Investigator Status: {investigator_h.get('status')}, Historical Cases: {investigator_h.get('retrieval_engine_cases')}")
    except Exception as e:
        print(f"  [FAIL] Investigator offline: {e}")
        return 1

    # Check background monitor status
    mon_status = http_get(f"{INVESTIGATOR_URL}/api/shopease/monitoring/status")
    mon_info = mon_status.get("monitoring", {})
    print(f"  [PASS] Background Monitor: is_running={mon_info.get('is_running')}, polls={mon_info.get('polls_count')}, interval={mon_info.get('polling_interval_seconds')}s")
    assert mon_info.get("is_running") is True, "Background monitor is not running!"

    # Ensure all faults are cleared first
    http_post(f"{SHOPEASE_URL}/api/faults/reset")
    time.sleep(1)

    # 2. Inject fault directly into ShopEase
    print("\n[Step 2] Injecting 'db_exhaustion' directly into ShopEase...")
    inj_res = http_post(f"{SHOPEASE_URL}/api/faults/inject", {"scenario": "db_exhaustion"})
    print(f"  [OK] Injected: {inj_res.get('message')}")

    # 3. Wait for background monitoring daemon to detect sustained anomaly
    print("\n[Step 3] Waiting for Autonomous Background Monitor to detect anomaly (interval 3s, threshold 2)...")
    detected_incident_id = None
    start_time = time.time()
    max_wait = 25  # seconds

    while time.time() - start_time < max_wait:
        time.sleep(2)
        mon = http_get(f"{INVESTIGATOR_URL}/api/shopease/monitoring/status").get("monitoring", {})
        print(f"  ... Polling state: streak={mon.get('consecutive_anomalies')}/{mon.get('consecutive_threshold')}, active_id={mon.get('active_incident_id')}")
        if mon.get("active_incident_id"):
            detected_incident_id = mon.get("active_incident_id")
            print(f"  [PASS] Autonomous Daemon detected sustained anomaly! Incident ID: {detected_incident_id}")
            break

    assert detected_incident_id is not None, "Background monitor failed to create incident within 25 seconds!"

    # 4. Inspect created incident
    print(f"\n[Step 4] Inspecting incident [{detected_incident_id}] in SQLite...")
    inc = http_get(f"{INVESTIGATOR_URL}/api/incidents/{detected_incident_id}")
    print(f"  Target System:    {inc.get('target_system')}")
    print(f"  Status:           {inc.get('status')}")
    print(f"  Culprit Service:  {inc.get('culprit_service')}")
    print(f"  Proposed Action:  {inc.get('proposed_action')}")
    print(f"  Confidence Score: {inc.get('confidence_score')}")
    print(f"  RCA Summary:      {inc.get('rca_summary')[:100]}...")

    assert inc.get("target_system") == "shopease"
    assert inc.get("status") == "AWAITING_APPROVAL", f"Expected AWAITING_APPROVAL, got {inc.get('status')}"
    assert inc.get("proposed_action") == "restart_connection_pool"
    print("  [PASS] Incident correctly placed in AWAITING_APPROVAL with allowlisted action.")

    # 5. Approve remediation (Human-in-the-Loop)
    print(f"\n[Step 5] Approving remediation for [{detected_incident_id}]...")
    app_res = http_post(
        f"{INVESTIGATOR_URL}/api/remediation/approve/{detected_incident_id}",
        {"approved": True, "approver_name": "Senior SRE (Automated Validation)"}
    )
    print(f"  [PASS] Status after approval: {app_res.get('incident', {}).get('status')}")
    assert app_res.get("incident", {}).get("status") == "APPROVED"

    # 6. Execute allowlisted remediation
    print(f"\n[Step 6] Executing remediation for [{detected_incident_id}]...")
    exec_res = http_post(
        f"{INVESTIGATOR_URL}/api/remediation/execute/{detected_incident_id}",
        {"incident_id": detected_incident_id, "simulate_verification_failure": False}
    )
    status_str = exec_res.get("status")
    inc_status = exec_res.get("incident_status") or exec_res.get("incident", {}).get("status")
    verif = exec_res.get("verification", {})
    verif_status = verif.get("status") if isinstance(verif, dict) else getattr(verif, "status", None)
    res_summary = exec_res.get("incident", {}).get("resolution_summary")

    print(f"  Execution status:    {status_str}")
    print(f"  Verification status: {verif_status}")
    print(f"  Incident status:     {inc_status}")
    print(f"  Resolution Summary:  {res_summary}")

    assert status_str == "success"
    assert verif_status == "PASSED"
    assert inc_status == "RESOLVED"
    print("  [PASS] Remediation executed, multi-SLO verification passed, incident RESOLVED!")

    # 7. Verify ShopEase is healthy again
    print("\n[Step 7] Verifying ShopEase restored to healthy state...")
    time.sleep(2)
    post_faults = http_get(f"{SHOPEASE_URL}/api/faults/status")
    print(f"  Active Faults in ShopEase: {post_faults.get('data', {}).get('activeFaults', [])}")
    assert len(post_faults.get("data", {}).get("activeFaults", [])) == 0

    mon_final = http_get(f"{INVESTIGATOR_URL}/api/shopease/monitoring/status").get("monitoring", {})
    print(f"  Monitor state: consecutive_healthy={mon_final.get('consecutive_healthy')}, consecutive_anomalies={mon_final.get('consecutive_anomalies')}")
    print("\n" + "=" * 80)
    print("  ALL REAL-TIME AUTONOMOUS CLOSED-LOOP VALIDATION CHECKS PASSED!")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())

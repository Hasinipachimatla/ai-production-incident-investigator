import json
import pytest
from app.services.fault_simulator import fault_simulator
from app.services.remediation_service import remediation_service
from app.models.incident import Incident
from app.core.allowlist import validate_action

def test_allowlist_validator():
    # Valid allowlisted action
    valid, msg = validate_action("restart_connection_pool", {"pool_size": 25})
    assert valid is True

    # Unknown hazardous action must fail
    invalid, err = validate_action("drop_table_users")
    assert invalid is False
    assert "NOT in the safe allowlist" in err

    # Disallowed parameters must fail
    invalid_param, err2 = validate_action("restart_connection_pool", {"destructive_purge": True})
    assert invalid_param is False
    assert "not allowed" in err2

def test_closed_loop_successful_recovery(db_session):
    fault_simulator.reset_all_faults()
    fault_simulator.trigger_fault("database_connection_exhaustion")

    # 1. Create Incident in AWAITING_APPROVAL status
    inc = Incident(
        id="INC-TEST-001",
        title="Test Database Connection Pool Saturation",
        status="AWAITING_APPROVAL",
        culprit_service="checkout-service",
        severity="CRITICAL",
        symptoms="DB connection pool 100%, 500 errors",
        proposed_action="restart_connection_pool",
        action_params_json=json.dumps({"pool_size": 20}),
        metrics_json=json.dumps(fault_simulator.get_current_metrics()),
        retry_count=0,
        max_retries=3
    )
    db_session.add(inc)
    db_session.commit()

    # 2. Verify execution blocked if not approved
    with pytest.raises(ValueError):
        remediation_service.execute_and_verify(db_session, inc)

    # 3. Explicit human approval
    remediation_service.approve_remediation(
        db=db_session,
        incident=inc,
        approved=True,
        approver_name="DevOps-Lead-Alice"
    )
    assert inc.status == "APPROVED"
    assert inc.approved_by == "DevOps-Lead-Alice"

    # 4. Execute remediation & verify actual recovery
    exec_res = remediation_service.execute_and_verify(
        db=db_session,
        incident=inc,
        simulate_verification_failure=False
    )

    assert exec_res["incident"].status == "RESOLVED"
    assert exec_res["verification"]["status"] == "PASSED"
    assert not fault_simulator.is_fault_active("database_connection_exhaustion")
    assert "all SLOs restored" in inc.resolution_summary

def test_closed_loop_retry_and_escalation_loop(db_session):
    fault_simulator.reset_all_faults()
    fault_simulator.trigger_fault("high_latency_cascade")

    inc = Incident(
        id="INC-TEST-RETRY",
        title="Payment Gateway Timeout Cascade",
        status="APPROVED",
        culprit_service="payment-gateway",
        severity="HIGH",
        symptoms="P99 latency > 4800ms",
        proposed_action="rate_limit_throttle",
        action_params_json=json.dumps({"throttle_pct": 25}),
        retry_count=0,
        max_retries=2
    )
    db_session.add(inc)
    db_session.commit()

    # 1. First execution attempt with simulated verification failure
    res1 = remediation_service.execute_and_verify(
        db=db_session,
        incident=inc,
        simulate_verification_failure=True
    )
    assert res1["verification"]["status"] == "FAILED"
    assert inc.retry_count == 1
    # System returns to AWAITING_APPROVAL with re-investigated proposal
    assert inc.status == "AWAITING_APPROVAL"
    assert "Retry" in inc.rca_summary

    # 2. Operator re-approves for retry #2
    remediation_service.approve_remediation(
        db=db_session,
        incident=inc,
        approved=True,
        approver_name="Operator-Bob"
    )
    assert inc.status == "APPROVED"

    # 3. Second execution attempt also fails -> Exceeds max_retries (2)
    res2 = remediation_service.execute_and_verify(
        db=db_session,
        incident=inc,
        simulate_verification_failure=True
    )
    assert inc.retry_count == 2
    assert inc.status == "FAILED_ESCALATED"
    assert "Safely escalated to human incident commander" in inc.resolution_summary

def test_ineffective_action_fails_verification(db_session):
    """
    Test Path A & Path B end to end:
    1. Ineffective but allowlisted action is executed.
    2. Fault remains active, verification fails, incident remains OPEN.
    3. Re-investigation proposes corrective action.
    4. Corrective action executed -> verification passes -> incident RESOLVED.
    """
    fault_simulator.reset_all_faults()
    fault_simulator.trigger_fault("database_connection_exhaustion")

    # Incident with ineffective allowlisted action (rate_limit_throttle does not fix DB connection pool)
    inc = Incident(
        id="INC-INEFFECTIVE-001",
        title="Database Exhaustion with Ineffective Fix",
        status="AWAITING_APPROVAL",
        culprit_service="checkout-service",
        severity="CRITICAL",
        symptoms="Database connection pool 100% full",
        proposed_action="rate_limit_throttle",
        action_params_json=json.dumps({"throttle_pct": 20}),
        metrics_json=json.dumps(fault_simulator.get_current_metrics()),
        retry_count=0,
        max_retries=3
    )
    db_session.add(inc)
    db_session.commit()

    # Approve the ineffective action
    remediation_service.approve_remediation(db_session, inc, approved=True, approver_name="Operator-Charlie")

    # Execute ineffective action (simulate_verification_failure=False -> relies on real state!)
    exec_res1 = remediation_service.execute_and_verify(db_session, inc, simulate_verification_failure=False)

    # Verification must fail because DB fault is still active
    assert exec_res1["verification"]["status"] == "FAILED"
    assert fault_simulator.is_fault_active("database_connection_exhaustion")
    assert inc.retry_count == 1
    assert inc.status == "AWAITING_APPROVAL"
    # Re-investigation refreshed proposal to the correct action
    assert inc.proposed_action == "restart_connection_pool"

    # Approve correct action for retry
    remediation_service.approve_remediation(db_session, inc, approved=True, approver_name="Lead-Architect")
    assert inc.status == "APPROVED"

    # Execute correct action
    exec_res2 = remediation_service.execute_and_verify(db_session, inc, simulate_verification_failure=False)
    assert exec_res2["verification"]["status"] == "PASSED"
    assert inc.status == "RESOLVED"
    assert not fault_simulator.is_fault_active("database_connection_exhaustion")

def test_invalid_state_transitions(db_session):
    """Verify system blocks unauthorized approvals, duplicate executions, and invalid state transitions."""
    inc = Incident(
        id="INC-STATE-001",
        title="State Machine Integrity Test",
        status="RESOLVED",
        culprit_service="checkout-service",
        severity="LOW",
        symptoms="Nominal",
        proposed_action="restart_connection_pool",
        action_params_json=json.dumps({}),
        retry_count=0,
        max_retries=3
    )
    db_session.add(inc)
    db_session.commit()

    # Cannot approve an already RESOLVED incident
    with pytest.raises(ValueError) as exc1:
        remediation_service.approve_remediation(db_session, inc, approved=True, approver_name="Hacker")
    assert "Invalid state transition" in str(exc1.value)

    # Set status to REJECTED
    inc.status = "REJECTED"
    db_session.commit()
    with pytest.raises(ValueError) as exc2:
        remediation_service.approve_remediation(db_session, inc, approved=True, approver_name="Hacker")
    assert "Invalid state transition" in str(exc2.value)

    # Set status to AWAITING_APPROVAL and attempt execute without approval
    inc.status = "AWAITING_APPROVAL"
    db_session.commit()
    with pytest.raises(ValueError) as exc3:
        remediation_service.execute_and_verify(db_session, inc)
    assert "Must be APPROVED or RETRYING" in str(exc3.value)

def test_independent_recovery_verification():
    """Verify recovery verifier independently assesses multiple telemetry dimensions."""
    from app.services.recovery_verifier import recovery_verifier

    fault_simulator.reset_all_faults()
    pre_metrics = fault_simulator.get_current_metrics()

    # When all nominal, verification passes
    res_healthy = recovery_verifier.verify_recovery("INC-01", "checkout-service", pre_metrics)
    assert res_healthy["status"] == "PASSED"
    assert res_healthy["slo_checks"]["error_rate_normal"] is True
    assert res_healthy["slo_checks"]["db_pool_healthy"] is True
    assert res_healthy["slo_checks"]["service_fault_cleared"] is True

    # When fault is active, verification fails independently
    fault_simulator.trigger_fault("database_connection_exhaustion")
    res_faulty = recovery_verifier.verify_recovery("INC-01", "checkout-service", pre_metrics)
    assert res_faulty["status"] == "FAILED"
    assert res_faulty["slo_checks"]["db_pool_healthy"] is False
    assert res_faulty["slo_checks"]["service_fault_cleared"] is False
    fault_simulator.reset_all_faults()


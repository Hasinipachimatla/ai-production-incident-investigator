from app.services.rca_engine import rca_engine
from app.core.allowlist import ALLOWLISTED_REMEDIATION_ACTIONS

def test_rca_engine_database_failure():
    metrics = {
        "db_pool_utilization_pct": 100.0,
        "error_rate_pct": 38.5,
        "p99_latency_ms": 3200.0
    }
    logs = [
        {
            "level": "ERROR",
            "service": "checkout-service",
            "message": "TimeoutError: QueuePool limit of size 100 reached connection timed out"
        },
        {
            "level": "CRITICAL",
            "service": "checkout-service",
            "message": "OperationalError: remaining connection slots reserved"
        }
    ]
    symptoms = "Database pool saturated causing checkout failure"

    rca = rca_engine.perform_rca(
        symptoms=symptoms,
        metrics=metrics,
        logs=logs
    )

    assert rca["culprit_service"] == "checkout-service"
    assert rca["confidence_score"] >= 0.70
    assert len(rca["evidence"]) >= 2
    assert rca["proposed_action"] == "restart_connection_pool"
    assert rca["proposed_action"] in ALLOWLISTED_REMEDIATION_ACTIONS
    assert rca["risk_level"] == "LOW"

def test_rca_engine_cache_failure():
    metrics = {
        "cache_hit_rate_pct": 12.0,
        "db_cpu_pct": 98.0,
        "error_rate_pct": 14.0
    }
    logs = [
        {
            "level": "WARN",
            "service": "catalog-service",
            "message": "RedisCacheMiss: bulk key prefix product_cat_ expired"
        }
    ]
    symptoms = "Cache miss storm degrading catalog response"

    rca = rca_engine.perform_rca(
        symptoms=symptoms,
        metrics=metrics,
        logs=logs
    )

    assert rca["culprit_service"] == "catalog-service"
    assert rca["proposed_action"] == "flush_and_warm_cache"
    assert rca["proposed_action"] in ALLOWLISTED_REMEDIATION_ACTIONS

def test_ground_truth_isolation_in_rca():
    """Verify live RCA signature has no parameters or leakage of ground truth labels."""
    import inspect
    sig = inspect.signature(rca_engine.perform_rca)
    params = list(sig.parameters.keys())
    assert "ground_truth" not in params
    assert "ground_truth_ids" not in params
    assert "label" not in params

def test_rca_evidence_correlation_and_confidence():
    """Verify RCA produces confidence explanation, safety rationale, and evidence classification."""
    metrics = {
        "db_pool_utilization_pct": 100.0,
        "error_rate_pct": 35.0,
        "p99_latency_ms": 3100.0
    }
    logs = [
        {"level": "ERROR", "service": "checkout-service", "message": "QueuePool limit of size 100 reached"}
    ]
    symptoms = "Database pool saturated causing checkout failure"

    rca = rca_engine.perform_rca(symptoms, metrics, logs)

    assert "confidence_explanation" in rca
    assert "0.70" in rca["confidence_explanation"]
    assert "safety_rationale" in rca
    assert "reversible" in rca["safety_rationale"].lower()
    assert "supporting_evidence" in rca
    assert "contradictory_evidence" in rca
    assert len(rca["supporting_evidence"]) > 0

def test_rca_novel_incident_heuristic_fallback():
    """Verify RCA handles novel out-of-domain failure cleanly with heuristic fallback."""
    metrics = {
        "p99_latency_ms": 4900.0,
        "error_rate_pct": 25.0
    }
    logs = [
        {"level": "WARN", "service": "payment-gateway", "message": "Upstream timeout waiting for external bank webhook"}
    ]
    symptoms = "Unprecedented exotic payment gateway timeout"

    rca = rca_engine.perform_rca(symptoms, metrics, logs)
    assert rca["culprit_service"] == "payment-gateway"
    assert rca["proposed_action"] in ALLOWLISTED_REMEDIATION_ACTIONS
    assert rca["confidence_score"] > 0.60
    assert "confidence_explanation" in rca


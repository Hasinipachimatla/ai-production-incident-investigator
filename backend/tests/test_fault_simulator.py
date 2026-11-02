import pytest
from app.services.fault_simulator import fault_simulator, FAULT_SCENARIOS, HEALTHY_BASELINE_METRICS

def test_fault_catalog():
    catalog = fault_simulator.get_catalog()
    assert len(catalog) >= 5
    types = [item["fault_type"] for item in catalog]
    assert "database_connection_exhaustion" in types
    assert "high_latency_cascade" in types
    assert "service_error_spike" in types
    assert "cache_invalidation_storm" in types
    assert "circuit_breaker_trip" in types

def test_trigger_and_reset_database_fault():
    fault_simulator.reset_all_faults()
    assert not fault_simulator.is_fault_active()

    # Trigger database connection pool fault
    res = fault_simulator.trigger_fault("database_connection_exhaustion")
    assert res["status"] == "triggered"
    assert fault_simulator.is_fault_active("database_connection_exhaustion")

    # Check metrics reflecting fault impact
    metrics = fault_simulator.get_current_metrics()
    assert metrics["db_pool_utilization_pct"] == 100.0
    assert metrics["error_rate_pct"] > 30.0

    # Check error logs generated
    logs = fault_simulator.get_recent_logs()
    assert len(logs) > 0
    assert any("QueuePool" in l["message"] for l in logs)

    # Reset fault
    reset_res = fault_simulator.reset_fault("database_connection_exhaustion")
    assert reset_res["status"] == "reset"
    assert not fault_simulator.is_fault_active("database_connection_exhaustion")

    # Metrics restored to baseline
    restored_metrics = fault_simulator.get_current_metrics()
    assert restored_metrics["db_pool_utilization_pct"] == HEALTHY_BASELINE_METRICS["db_pool_utilization_pct"]
    assert restored_metrics["error_rate_pct"] == HEALTHY_BASELINE_METRICS["error_rate_pct"]

def test_invalid_fault_trigger():
    with pytest.raises(ValueError) as exc:
        fault_simulator.trigger_fault("non_existent_destructive_fault")
    assert "Unknown fault scenario" in str(exc.value)

def test_reset_all_faults():
    fault_simulator.trigger_fault("high_latency_cascade")
    fault_simulator.trigger_fault("service_error_spike")
    assert len(fault_simulator.get_active_fault_names()) == 2

    res = fault_simulator.reset_all_faults()
    assert res["status"] == "reset_all"
    assert res["reset_count"] == 2
    assert len(fault_simulator.get_active_fault_names()) == 0

def test_all_five_fault_scenarios():
    """Verify each of the 5 fault scenarios has initial condition, trigger, symptoms, recovery action, and safe reset."""
    scenarios = [
        ("database_connection_exhaustion", "checkout-service", "restart_connection_pool", "db_pool_utilization_pct", 100.0),
        ("high_latency_cascade", "payment-gateway", "rate_limit_throttle", "p99_latency_ms", 4920.0),
        ("service_error_spike", "inventory-api", "rollback_config_flag", "error_rate_pct", 52.4),
        ("cache_invalidation_storm", "catalog-service", "flush_and_warm_cache", "cache_hit_rate_pct", 12.2),
        ("circuit_breaker_trip", "recommendation-service", "reset_circuit_breaker", "circuit_breaker_state", "OPEN")
    ]

    for fault_type, target_svc, expected_action, impact_key, impact_val in scenarios:
        fault_simulator.reset_all_faults()
        assert not fault_simulator.is_fault_active()

        # Trigger
        trig = fault_simulator.trigger_fault(fault_type)
        assert trig["status"] == "triggered"
        assert trig["target_service"] == target_svc
        assert fault_simulator.is_fault_active(fault_type)

        # Observable symptoms
        metrics = fault_simulator.get_current_metrics()
        assert metrics[impact_key] == impact_val

        # Expected evidence logs
        logs = fault_simulator.get_recent_logs()
        assert len(logs) > 0
        assert any(l["service"] == target_svc for l in logs)

        # Expected recovery action
        catalog_entry = next(item for item in fault_simulator.get_catalog() if item["fault_type"] == fault_type)
        assert catalog_entry["expected_remediation"] == expected_action
        assert catalog_entry["reversible"] is True

        # Safe reset
        reset_res = fault_simulator.reset_fault(fault_type)
        assert reset_res["status"] == "reset"
        assert not fault_simulator.is_fault_active(fault_type)
        metrics_restored = fault_simulator.get_current_metrics()
        assert metrics_restored["error_rate_pct"] == HEALTHY_BASELINE_METRICS["error_rate_pct"]


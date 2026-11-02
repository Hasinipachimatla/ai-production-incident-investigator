import time
from typing import Dict, Any
from app.services.fault_simulator import fault_simulator, FAULT_SCENARIOS

class RecoveryVerifier:
    def __init__(self):
        pass

    def verify_recovery(
        self,
        incident_id: str,
        culprit_service: str,
        pre_metrics: Dict[str, Any],
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        """
        Verifies actual recovery following remediation action.
        If simulate_failure is True, artificially forces verification to fail
        to validate the closed-loop re-investigation and retry limit logic.
        """
        # Collect post-remediation metrics
        post_metrics = fault_simulator.get_current_metrics()

        active_fault_names = fault_simulator.get_active_fault_names()
        service_fault_active = any(
            FAULT_SCENARIOS.get(f, {}).get("target_service") == culprit_service
            for f in active_fault_names
        )

        slo_checks = {
            "error_rate_normal": bool(post_metrics.get("error_rate_pct", 0) <= 2.0),
            "latency_normal": bool(post_metrics.get("p99_latency_ms", 0) <= 500.0),
            "db_pool_healthy": bool(post_metrics.get("db_pool_utilization_pct", 0) <= 80.0),
            "circuit_breaker_closed": bool(post_metrics.get("circuit_breaker_state", "CLOSED") != "OPEN"),
            "cache_healthy": bool(post_metrics.get("cache_hit_rate_pct", 100) >= 60.0),
            "service_fault_cleared": not service_fault_active
        }

        # If simulate_failure is forced for closed-loop research test, override
        if simulate_failure:
            slo_checks["simulated_fault_injection"] = False
            all_passed = False
            details = (
                "Post-remediation verification FAILED: Synthetic fault verification test triggered. "
                "SLO check failed to recover. System keeping incident OPEN for re-investigation and safe retry."
            )
        else:
            all_passed = all(slo_checks.values())
            if all_passed:
                details = (
                    f"Post-remediation verification PASSED: Service '{culprit_service}' confirmed recovered. "
                    f"Error rate: {post_metrics.get('error_rate_pct')}%, "
                    f"P99 latency: {post_metrics.get('p99_latency_ms')}ms. "
                    "All SLO requirements satisfied."
                )
            else:
                failed_checks = [k for k, v in slo_checks.items() if not v]
                details = (
                    f"Post-remediation verification FAILED: Failed checks: {failed_checks}. "
                    "Service has not returned to normal baseline. Incident remains open for retry."
                )

        return {
            "status": "PASSED" if all_passed else "FAILED",
            "incident_id": incident_id,
            "culprit_service": culprit_service,
            "pre_metrics": pre_metrics,
            "post_metrics": post_metrics,
            "slo_checks": slo_checks,
            "details": details
        }

recovery_verifier = RecoveryVerifier()

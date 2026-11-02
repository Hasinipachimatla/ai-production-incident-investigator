import time
from datetime import datetime
from typing import Dict, Any, List, Optional

FAULT_SCENARIOS = {
    "database_connection_exhaustion": {
        "fault_type": "database_connection_exhaustion",
        "name": "Database Connection Pool Exhaustion",
        "target_service": "checkout-service",
        "description": "Simulates unreleased checkout connections saturating the connection pool to 100%, triggering connection timeouts and 500 errors.",
        "reversible": True,
        "symptoms": "Spike in HTTP 500 errors, QueuePool limit reached, timeout waiting for available database connection slot.",
        "expected_remediation": "restart_connection_pool",
        "metrics_impact": {
            "db_pool_utilization_pct": 100.0,
            "error_rate_pct": 38.5,
            "p99_latency_ms": 3250.0,
            "cpu_percent": 74.0,
            "requests_per_sec": 420.0,
            "cache_hit_rate_pct": 89.0
        },
        "log_templates": [
            "[ERROR] checkout-service: TimeoutError: QueuePool limit of size 100 overflow 20 reached, connection timed out, timeout 30.00s",
            "[CRITICAL] checkout-service: OperationalError: remaining connection slots are reserved for non-replication superuser connections",
            "[ERROR] checkout-service: HTTP 500 Internal Server Error returned on /api/v1/checkout/confirm"
        ]
    },
    "high_latency_cascade": {
        "fault_type": "high_latency_cascade",
        "name": "Downstream Payment Gateway Latency Spike",
        "target_service": "payment-gateway",
        "description": "Simulates slow third-party webhook responses causing worker thread starvation and 504 gateway timeouts.",
        "reversible": True,
        "symptoms": "P99 latency degraded to >4800ms, worker threads waiting on upstream socket read, worker queue depth surging.",
        "expected_remediation": "rate_limit_throttle",
        "metrics_impact": {
            "db_pool_utilization_pct": 28.0,
            "error_rate_pct": 21.0,
            "p99_latency_ms": 4920.0,
            "cpu_percent": 52.0,
            "worker_queue_depth": 580,
            "requests_per_sec": 290.0
        },
        "log_templates": [
            "[WARN] payment-gateway: Upstream socket read duration 4850ms exceeded SLA threshold 1000ms",
            "[ERROR] payment-gateway: requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='pay-partner.internal'): Read timed out",
            "[WARN] payment-gateway: Thread starvation: active worker pool 98% busy with backlog queue 580 items"
        ]
    },
    "service_error_spike": {
        "fault_type": "service_error_spike",
        "name": "Unhandled Null Pointer Schema Regression",
        "target_service": "inventory-api",
        "description": "Simulates unexpected missing field in stock payload causing unhandled exceptions and 500 error cascade.",
        "reversible": True,
        "symptoms": "52% HTTP 500 error rate on /api/v1/inventory/reserve, AttributeError stack traces in logs.",
        "expected_remediation": "rollback_config_flag",
        "metrics_impact": {
            "db_pool_utilization_pct": 20.0,
            "error_rate_pct": 52.4,
            "p99_latency_ms": 185.0,
            "cpu_percent": 38.0,
            "requests_per_sec": 380.0
        },
        "log_templates": [
            "[ERROR] inventory-api: AttributeError: 'NoneType' object has no attribute 'warehouse_id' at inventory/service.py:142",
            "[ERROR] inventory-api: Unhandled exception during order item reservation payload processing",
            "[ERROR] inventory-api: HTTP 500 returned to client for transaction reservation txn_4492"
        ]
    },
    "cache_invalidation_storm": {
        "fault_type": "cache_invalidation_storm",
        "name": "Redis Cache Invalidation Storm",
        "target_service": "catalog-service",
        "description": "Simulates synchronized cache key expiration stampeding the catalog database replica with 10x query volume.",
        "reversible": True,
        "symptoms": "Cache hit ratio collapsed to 12%, database replica CPU at 98%, query latency degraded.",
        "expected_remediation": "flush_and_warm_cache",
        "metrics_impact": {
            "db_pool_utilization_pct": 72.0,
            "cache_hit_rate_pct": 12.2,
            "db_cpu_pct": 98.4,
            "p99_latency_ms": 2850.0,
            "error_rate_pct": 14.2,
            "requests_per_sec": 650.0
        },
        "log_templates": [
            "[WARN] catalog-service: RedisCacheMiss: bulk key prefix 'product_cat_' expired concurrently",
            "[WARN] catalog-service: Postgres replica CPU utilization > 95% for 3 consecutive check intervals",
            "[ERROR] catalog-service: SlowQueryLog: SELECT * FROM product_variants took 3980ms"
        ]
    },
    "circuit_breaker_trip": {
        "fault_type": "circuit_breaker_trip",
        "name": "Circuit Breaker Tripped in Recommendation Engine",
        "target_service": "recommendation-service",
        "description": "Simulates downstream vector search failure triggering circuit breaker to OPEN state, serving fallback widgets.",
        "reversible": True,
        "symptoms": "Endpoint returning HTTP 503 Circuit Breaker Open, zero live vector queries reaching model.",
        "expected_remediation": "reset_circuit_breaker",
        "metrics_impact": {
            "circuit_breaker_state": "OPEN",
            "error_rate_pct": 32.0,
            "p99_latency_ms": 95.0,
            "cpu_percent": 24.0,
            "fallback_request_pct": 100.0
        },
        "log_templates": [
            "[WARN] recommendation-service: CircuitBreakerOpenException: failure rate 68% exceeded trip threshold 50%",
            "[WARN] recommendation-service: Short-circuiting call to vector-similarity cluster",
            "[INFO] recommendation-service: Dispatched static fallback recommendation list"
        ]
    }
}

HEALTHY_BASELINE_METRICS = {
    "db_pool_utilization_pct": 18.0,
    "error_rate_pct": 0.15,
    "p99_latency_ms": 45.0,
    "cpu_percent": 22.0,
    "requests_per_sec": 450.0,
    "cache_hit_rate_pct": 96.5,
    "worker_queue_depth": 12,
    "circuit_breaker_state": "CLOSED"
}

class FaultSimulatorService:
    def __init__(self):
        self._active_faults: Dict[str, Dict[str, Any]] = {}
        self._last_triggered_at: Optional[str] = None

    def get_catalog(self) -> List[Dict[str, Any]]:
        return list(FAULT_SCENARIOS.values())

    def trigger_fault(self, fault_type: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if fault_type not in FAULT_SCENARIOS:
            raise ValueError(f"Unknown fault scenario: '{fault_type}'. Available: {list(FAULT_SCENARIOS.keys())}")
        
        scenario = FAULT_SCENARIOS[fault_type]
        now_iso = datetime.utcnow().isoformat()
        self._active_faults[fault_type] = {
            "fault_type": fault_type,
            "scenario": scenario,
            "parameters": parameters or {},
            "triggered_at": now_iso
        }
        self._last_triggered_at = now_iso
        return {
            "status": "triggered",
            "fault_type": fault_type,
            "name": scenario["name"],
            "target_service": scenario["target_service"],
            "triggered_at": now_iso
        }

    def reset_fault(self, fault_type: str) -> Dict[str, Any]:
        if fault_type in self._active_faults:
            removed = self._active_faults.pop(fault_type)
            return {
                "status": "reset",
                "fault_type": fault_type,
                "message": f"Fault '{fault_type}' successfully reset to normal state."
            }
        return {
            "status": "not_active",
            "fault_type": fault_type,
            "message": f"Fault '{fault_type}' was not active."
        }

    def reset_all_faults(self) -> Dict[str, Any]:
        count = len(self._active_faults)
        self._active_faults.clear()
        return {
            "status": "reset_all",
            "reset_count": count,
            "message": f"All {count} active faults cleared. System returned to healthy baseline."
        }

    def is_fault_active(self, fault_type: Optional[str] = None) -> bool:
        if fault_type:
            return fault_type in self._active_faults
        return len(self._active_faults) > 0

    def get_active_fault_names(self) -> List[str]:
        return list(self._active_faults.keys())

    def get_current_metrics(self) -> Dict[str, Any]:
        metrics = dict(HEALTHY_BASELINE_METRICS)
        # Apply impacts of active faults
        for fault_info in self._active_faults.values():
            scenario = fault_info["scenario"]
            impact = scenario.get("metrics_impact", {})
            for k, v in impact.items():
                metrics[k] = v
        metrics["active_fault_count"] = len(self._active_faults)
        metrics["timestamp"] = datetime.utcnow().isoformat()
        return metrics

    def get_recent_logs(self, limit: int = 15) -> List[Dict[str, Any]]:
        logs = []
        now_ts = datetime.utcnow().isoformat()
        if not self._active_faults:
            logs.append({
                "timestamp": now_ts,
                "level": "INFO",
                "service": "api-gateway",
                "message": "Gateway operating within nominal limits (p99: 45ms, error_rate: 0.15%)"
            })
            logs.append({
                "timestamp": now_ts,
                "level": "INFO",
                "service": "checkout-service",
                "message": "Health check OK: connection pool usage 18%, db ping 1.2ms"
            })
            return logs

        for fault_info in self._active_faults.values():
            scenario = fault_info["scenario"]
            for tmpl in scenario.get("log_templates", []):
                level = "ERROR" if "[ERROR]" in tmpl else ("CRITICAL" if "[CRITICAL]" in tmpl else "WARN")
                clean_msg = tmpl.replace("[ERROR] ", "").replace("[CRITICAL] ", "").replace("[WARN] ", "")
                logs.append({
                    "timestamp": now_ts,
                    "level": level,
                    "service": scenario["target_service"],
                    "message": clean_msg
                })
        return logs[:limit]

# Singleton instance
fault_simulator = FaultSimulatorService()

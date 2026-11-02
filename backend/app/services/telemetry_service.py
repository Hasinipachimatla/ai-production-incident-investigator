from typing import Dict, Any, List
from app.services.fault_simulator import fault_simulator

SLO_THRESHOLDS = {
    "error_rate_pct": {"threshold": 2.0, "operator": ">", "metric_name": "Error Rate (%)"},
    "p99_latency_ms": {"threshold": 500.0, "operator": ">", "metric_name": "P99 Latency (ms)"},
    "db_pool_utilization_pct": {"threshold": 80.0, "operator": ">", "metric_name": "DB Pool Utilization (%)"},
    "cache_hit_rate_pct": {"threshold": 60.0, "operator": "<", "metric_name": "Cache Hit Rate (%)"},
    "circuit_breaker_state": {"threshold": "OPEN", "operator": "==", "metric_name": "Circuit Breaker State"}
}

class TelemetryService:
    def __init__(self):
        pass

    def collect_snapshot(self) -> Dict[str, Any]:
        metrics = fault_simulator.get_current_metrics()
        logs = fault_simulator.get_recent_logs(limit=20)
        anomalies = self.detect_anomalies(metrics)
        return {
            "metrics": metrics,
            "logs": logs,
            "anomalies": anomalies,
            "anomaly_detected": len(anomalies) > 0
        }

    def detect_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        anomalies = []
        for metric_key, rule in SLO_THRESHOLDS.items():
            if metric_key in metrics:
                val = metrics[metric_key]
                thresh = rule["threshold"]
                op = rule["operator"]
                breached = False
                if op == ">" and isinstance(val, (int, float)) and val > thresh:
                    breached = True
                elif op == "<" and isinstance(val, (int, float)) and val < thresh:
                    breached = True
                elif op == "==" and val == thresh:
                    breached = True
                
                if breached:
                    anomalies.append({
                        "metric": metric_key,
                        "label": rule["metric_name"],
                        "current_value": val,
                        "threshold": thresh,
                        "operator": op,
                        "severity": "CRITICAL" if (metric_key in ["error_rate_pct", "db_pool_utilization_pct"] and (isinstance(val, (int, float)) and val > 30)) else "WARNING"
                    })
        return anomalies

telemetry_service = TelemetryService()

from typing import Dict, Any, Optional

ALLOWLISTED_REMEDIATION_ACTIONS: Dict[str, Dict[str, Any]] = {
    "restart_connection_pool": {
        "name": "restart_connection_pool",
        "description": "Drain leaked and hanging connections, safely reset the database connection pool, and re-establish clean connection limits.",
        "risk_level": "LOW",
        "reversible": True,
        "target_service": "database-cluster",
        "allowed_parameters": ["pool_size", "max_overflow", "recycle_timeout_sec"],
        "default_parameters": {
            "pool_size": 20,
            "max_overflow": 10,
            "recycle_timeout_sec": 30
        }
    },
    "rate_limit_throttle": {
        "name": "rate_limit_throttle",
        "description": "Apply temporary dynamic ingress rate throttling (token bucket) to protect downstream services and allow thread pool recovery.",
        "risk_level": "LOW",
        "reversible": True,
        "target_service": "payment-gateway",
        "allowed_parameters": ["throttle_pct", "duration_seconds", "client_segment"],
        "default_parameters": {
            "throttle_pct": 25,
            "duration_seconds": 60,
            "client_segment": "all"
        }
    },
    "flush_and_warm_cache": {
        "name": "flush_and_warm_cache",
        "description": "Purge corrupted or expired cache keys with staggered TTL jitter and warm primary catalog cache asynchronously.",
        "risk_level": "LOW",
        "reversible": True,
        "target_service": "catalog-service",
        "allowed_parameters": ["cache_prefix", "stagger_jitter_sec", "warm_async"],
        "default_parameters": {
            "cache_prefix": "product_cat_",
            "stagger_jitter_sec": 15,
            "warm_async": True
        }
    },
    "rollback_config_flag": {
        "name": "rollback_config_flag",
        "description": "Safely revert recent schema validation flag or feature flag to previous stable configuration snapshot.",
        "risk_level": "LOW",
        "reversible": True,
        "target_service": "inventory-api",
        "allowed_parameters": ["flag_name", "target_version"],
        "default_parameters": {
            "flag_name": "require_strict_warehouse_id",
            "target_version": "v1.4.0"
        }
    },
    "reset_circuit_breaker": {
        "name": "reset_circuit_breaker",
        "description": "Force circuit breaker from OPEN to HALF_OPEN probe state with cautious canary sampling to resume traffic.",
        "risk_level": "LOW",
        "reversible": True,
        "target_service": "recommendation-service",
        "allowed_parameters": ["sample_request_limit", "consecutive_success_threshold"],
        "default_parameters": {
            "sample_request_limit": 10,
            "consecutive_success_threshold": 5
        }
    },
    "scale_worker_replicas": {
        "name": "scale_worker_replicas",
        "description": "Increment container worker replica count to absorb transient traffic surges or relieve memory pressure.",
        "risk_level": "MEDIUM",
        "reversible": True,
        "target_service": "order-service",
        "allowed_parameters": ["target_replicas", "scale_delta"],
        "default_parameters": {
            "target_replicas": 6,
            "scale_delta": 2
        }
    }
}

def validate_action(action_name: str, params: Optional[Dict[str, Any]] = None) -> tuple[bool, str]:
    """
    Strict allowlist gate validation.
    Returns (is_valid, error_message).
    """
    if not action_name:
        return False, "Remediation action name cannot be empty."
        
    if action_name not in ALLOWLISTED_REMEDIATION_ACTIONS:
        return False, (
            f"Action '{action_name}' is NOT in the safe allowlist. "
            f"Allowed actions: {list(ALLOWLISTED_REMEDIATION_ACTIONS.keys())}"
        )
        
    action_spec = ALLOWLISTED_REMEDIATION_ACTIONS[action_name]
    if params:
        allowed_param_keys = set(action_spec.get("allowed_parameters", []))
        provided_keys = set(params.keys())
        disallowed = provided_keys - allowed_param_keys
        if disallowed:
            return False, f"Parameters {list(disallowed)} are not allowed for action '{action_name}'."
            
    return True, "Action is validated and safe."

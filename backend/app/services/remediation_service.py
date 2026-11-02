import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.allowlist import validate_action, ALLOWLISTED_REMEDIATION_ACTIONS
from app.models.incident import Incident
from app.models.audit_log import IncidentAuditLog
from app.services.fault_simulator import fault_simulator
from app.services.recovery_verifier import recovery_verifier
from app.services.rca_engine import rca_engine

from app.services.shopease_adapter import shopease_adapter

# Map safe remediation actions to corresponding simulated fault reset
ACTION_TO_FAULT_MAP = {
    "restart_connection_pool": "database_connection_exhaustion",
    "rate_limit_throttle": "high_latency_cascade",
    "rollback_config_flag": "service_error_spike",
    "flush_and_warm_cache": "cache_invalidation_storm",
    "reset_circuit_breaker": "circuit_breaker_trip",
    "scale_worker_replicas": "high_latency_cascade"
}

class RemediationService:
    def __init__(self):
        pass

    def approve_remediation(
        self,
        db: Session,
        incident: Incident,
        approved: bool,
        approver_name: str,
        override_action: Optional[str] = None,
        override_params: Optional[Dict[str, Any]] = None,
        rejection_reason: Optional[str] = None
    ) -> Incident:
        if incident.status not in ["AWAITING_APPROVAL", "RETRYING"]:
            raise ValueError(
                f"Invalid state transition: Cannot approve incident {incident.id} in status '{incident.status}'. "
                "Only incidents in 'AWAITING_APPROVAL' or 'RETRYING' can be approved."
            )

        now = datetime.utcnow()
        if not approved:
            incident.status = "REJECTED"
            incident.approved_by = approver_name
            incident.rejection_reason = rejection_reason or "Rejected by operator."
            incident.updated_at = now
            self._log_audit(db, incident.id, "APPROVAL", "REJECTED", f"Rejected by {approver_name}: {incident.rejection_reason}")
            db.commit()
            db.refresh(incident)
            return incident

        target_action = override_action or incident.proposed_action
        target_params = override_params or (json.loads(incident.action_params_json) if incident.action_params_json else {})

        # Strictly validate action against safe allowlist
        is_valid, err = validate_action(target_action, target_params)
        if not is_valid:
            raise ValueError(f"Allowlist Security Gate Failed: {err}")

        incident.status = "APPROVED"
        incident.approved_by = approver_name
        incident.approval_timestamp = now
        incident.proposed_action = target_action
        incident.action_params_json = json.dumps(target_params)
        incident.updated_at = now

        self._log_audit(
            db, 
            incident.id, 
            "APPROVAL", 
            "APPROVED", 
            f"Approved by {approver_name} for action '{target_action}'."
        )
        db.commit()
        db.refresh(incident)
        return incident

    def execute_and_verify(
        self,
        db: Session,
        incident: Incident,
        simulate_verification_failure: bool = False
    ) -> Dict[str, Any]:
        if incident.status in ["REMEDIATING", "VERIFYING"]:
            raise ValueError(f"Duplicate execution blocked: Incident {incident.id} is already in state '{incident.status}'.")

        if incident.status not in ["APPROVED", "RETRYING"]:
            raise ValueError(f"Invalid state transition: Incident {incident.id} cannot be executed in status '{incident.status}'. Must be APPROVED or RETRYING.")

        now = datetime.utcnow()
        incident.status = "REMEDIATING"
        incident.executed_at = now
        db.commit()

        action_name = incident.proposed_action
        action_params = json.loads(incident.action_params_json) if incident.action_params_json else {}
        self._log_audit(db, incident.id, "EXECUTION", "IN_PROGRESS", f"Executing safe allowlisted action '{action_name}'.")

        is_shopease = getattr(incident, "target_system", "simulator") == "shopease"

        # Capture pre-remediation metrics snapshot
        if incident.metrics_json:
            pre_metrics = json.loads(incident.metrics_json)
        elif is_shopease:
            pre_metrics = shopease_adapter.collect_snapshot()["metrics"]
        else:
            pre_metrics = fault_simulator.get_current_metrics()

        # Execute remediation in target system
        if is_shopease:
            if not simulate_verification_failure:
                try:
                    shopease_adapter.execute_remediation(action_name, action_params)
                except Exception as e:
                    self._log_audit(db, incident.id, "EXECUTION", "ERROR", f"ShopEase control error: {str(e)}")

            # Step into VERIFYING phase
            incident.status = "VERIFYING"
            db.commit()
            self._log_audit(db, incident.id, "VERIFICATION", "IN_PROGRESS", "Gathering post-remediation ShopEase metrics for independent SLO verification.")

            # Run Independent Recovery Verifier for ShopEase
            verification_output = shopease_adapter.verify_recovery(
                incident_id=incident.id,
                culprit_service=incident.culprit_service,
                pre_metrics=pre_metrics,
                simulate_failure=simulate_verification_failure
            )
        else:
            # Execute remediation in simulated system
            if not simulate_verification_failure:
                target_fault = ACTION_TO_FAULT_MAP.get(action_name)
                if target_fault and fault_simulator.is_fault_active(target_fault):
                    fault_simulator.reset_fault(target_fault)

            # Step into VERIFYING phase
            incident.status = "VERIFYING"
            db.commit()
            self._log_audit(db, incident.id, "VERIFICATION", "IN_PROGRESS", "Gathering post-remediation metrics for SLO validation.")

            # Run Recovery Verifier
            verification_output = recovery_verifier.verify_recovery(
                incident_id=incident.id,
                culprit_service=incident.culprit_service,
                pre_metrics=pre_metrics,
                simulate_failure=simulate_verification_failure
            )

        incident.verified_at = datetime.utcnow()
        incident.verification_status = verification_output["status"]
        incident.verification_details_json = json.dumps(verification_output)

        if verification_output["status"] == "PASSED":
            # Successfully resolved closed loop
            incident.status = "RESOLVED"
            incident.resolution_summary = (
                f"Incident successfully resolved via allowlisted action '{action_name}'. "
                f"Independent verification confirmed all SLOs restored."
            )
            self._log_audit(db, incident.id, "RESOLUTION", "RESOLVED", incident.resolution_summary)
        else:
            # Verification failed: Handle retry & safe re-investigation loop
            incident.retry_count += 1
            if incident.retry_count < incident.max_retries:
                incident.status = "RETRYING"
                # Trigger re-investigation to adapt RCA and suggest alternative
                if is_shopease:
                    re_snapshot = shopease_adapter.collect_snapshot()
                    latest_metrics = re_snapshot["metrics"]
                    latest_logs = re_snapshot["logs"]
                else:
                    latest_metrics = fault_simulator.get_current_metrics()
                    latest_logs = fault_simulator.get_recent_logs()

                re_rca = rca_engine.perform_rca(
                    symptoms=f"{incident.symptoms} (Retry attempt #{incident.retry_count} after verification failure)",
                    metrics=latest_metrics,
                    logs=latest_logs,
                    culprit_service_hint=incident.culprit_service
                )
                incident.rca_summary = f"[Retry {incident.retry_count}/{incident.max_retries}] {re_rca['rca_summary']}"
                incident.proposed_action = re_rca["proposed_action"]
                incident.action_params_json = json.dumps(re_rca["action_params"])
                # Return to approval gate for safe human confirmation on retry
                incident.status = "AWAITING_APPROVAL"
                self._log_audit(
                    db,
                    incident.id,
                    "RETRY_INVESTIGATION",
                    f"RETRY_{incident.retry_count}",
                    f"Verification failed. Re-investigation proposed alternative action '{re_rca['proposed_action']}'. Awaiting re-approval."
                )
            else:
                incident.status = "FAILED_ESCALATED"
                incident.resolution_summary = (
                    f"Max remediation retries ({incident.max_retries}) reached without SLO recovery. "
                    "Safely escalated to human incident commander to prevent unbounded remediation attempts."
                )
                self._log_audit(db, incident.id, "ESCALATION", "FAILED_ESCALATED", incident.resolution_summary)

        db.commit()
        db.refresh(incident)

        return {
            "incident": incident,
            "verification": verification_output
        }

    def _log_audit(self, db: Session, incident_id: str, stage: str, action: str, details: str):
        log_entry = IncidentAuditLog(
            incident_id=incident_id,
            stage=stage,
            action_taken=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)

remediation_service = RemediationService()

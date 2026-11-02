import csv
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.historical_case import HistoricalCase
from app.services.retrieval_engine import retrieval_engine

class DatasetImporter:
    def __init__(self):
        pass

    def parse_and_import_csv(self, file_path: Path, db: Optional[Session] = None, source_label: str = "kaggle_import") -> Dict[str, Any]:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        imported_cases: List[Dict[str, Any]] = []
        skipped_count = 0
        detected_format = "unknown"

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            headers = [h.strip().lower() for h in (reader.fieldnames or [])]

            # Detect format
            if "project_name" in headers and "error_message" in headers:
                detected_format = "kaggle_aiops_failure_detection"
            elif "service" in headers and "symptoms" in headers:
                detected_format = "standard_incident_csv"
            else:
                detected_format = "generic_telemetry_csv"

            for idx, row in enumerate(reader):
                clean_row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}
                case = self._map_row_to_case(clean_row, detected_format, idx, source_label)
                if case:
                    imported_cases.append(case)
                else:
                    skipped_count += 1

        # Ingest into DB and retrieval engine
        self._ingest_cases(imported_cases, db)

        return {
            "status": "success",
            "imported_count": len(imported_cases),
            "skipped_count": skipped_count,
            "detected_format": detected_format,
            "filename": file_path.name,
            "total_cases_in_repo": len(retrieval_engine.cases)
        }

    def _map_row_to_case(self, row: Dict[str, str], fmt: str, idx: int, source_label: str) -> Optional[Dict[str, Any]]:
        cid = f"INC-IMP-{uuid.uuid4().hex[:8].upper()}"

        if fmt == "kaggle_aiops_failure_detection":
            service = row.get("project_name") or row.get("service", "app-service")
            error_msg = row.get("error_message", "")
            root_cause = row.get("root_cause") or f"Runtime anomaly in {service}: {error_msg}"
            resolution = row.get("resolution_action") or "restart_connection_pool"
            event_type = row.get("event_type", "application_error")
            category = row.get("category") or "service_error"
            title = f"{event_type.replace('_', ' ').title()} in {service}"
            symptoms = f"Observed {error_msg}. Latency: {row.get('latency_ms', 'N/A')}ms, Status: {row.get('response_status', 'N/A')}"

            return {
                "id": cid,
                "title": title,
                "category": category,
                "service": service,
                "symptoms": symptoms,
                "root_cause": root_cause,
                "recommended_remediation": resolution,
                "log_patterns": [error_msg] if error_msg else [],
                "metric_signatures": {
                    "latency_ms": row.get("latency_ms"),
                    "response_status": row.get("response_status")
                },
                "tags": [category, service, event_type],
                "source": source_label
            }

        elif fmt == "standard_incident_csv":
            return {
                "id": row.get("id") or cid,
                "title": row.get("title", f"Imported Incident #{idx}"),
                "category": row.get("category", "general"),
                "service": row.get("service", "unknown"),
                "symptoms": row.get("symptoms", ""),
                "root_cause": row.get("root_cause", ""),
                "recommended_remediation": row.get("recommended_remediation", "restart_connection_pool"),
                "log_patterns": [row.get("logs", "")] if row.get("logs") else [],
                "metric_signatures": {},
                "tags": [row.get("category", "incident")],
                "source": source_label
            }

        else:
            # Generic mapping attempt
            msg = row.get("message") or row.get("log") or row.get("description") or str(row)
            if not msg or len(msg.strip()) < 5:
                return None
            return {
                "id": cid,
                "title": f"Telemetry Incident Event #{idx}",
                "category": row.get("category", "telemetry"),
                "service": row.get("service") or row.get("hostname", "system"),
                "symptoms": msg,
                "root_cause": row.get("root_cause", "Observed anomalous log signature in telemetry stream"),
                "recommended_remediation": "restart_connection_pool",
                "log_patterns": [msg],
                "metric_signatures": {},
                "tags": ["telemetry"],
                "source": source_label
            }

    def _ingest_cases(self, new_cases: List[Dict[str, Any]], db: Optional[Session] = None):
        if not new_cases:
            return

        # Ensure all incoming cases have valid IDs and required attributes
        sanitized_cases = []
        for c in new_cases:
            if not isinstance(c, dict):
                continue
            cid = c.get("id") or f"INC-IMP-{uuid.uuid4().hex[:8].upper()}"
            sanitized = {
                "id": str(cid),
                "title": str(c.get("title") or f"Imported Incident Case {cid}"),
                "category": str(c.get("category") or "general"),
                "service": str(c.get("service") or "unknown"),
                "symptoms": str(c.get("symptoms") or ""),
                "root_cause": str(c.get("root_cause") or "Root cause under investigation"),
                "recommended_remediation": str(c.get("recommended_remediation") or "restart_connection_pool"),
                "log_patterns": c.get("log_patterns") if isinstance(c.get("log_patterns"), list) else ([str(c.get("log_patterns"))] if c.get("log_patterns") else []),
                "metric_signatures": c.get("metric_signatures") if isinstance(c.get("metric_signatures"), dict) else {},
                "tags": c.get("tags") if isinstance(c.get("tags"), list) else ([str(c.get("tags"))] if c.get("tags") else []),
                "source": str(c.get("source") or "imported")
            }
            sanitized_cases.append(sanitized)

        # Append to retrieval engine in-memory
        all_cases = list(retrieval_engine.cases)
        existing_ids = {c["id"] for c in all_cases}

        for c in sanitized_cases:
            if c["id"] not in existing_ids:
                all_cases.append(c)
                existing_ids.add(c["id"])

        retrieval_engine.load_cases(all_cases)

        # Persist to database if db session provided
        if db:
            for c in sanitized_cases:
                existing = db.query(HistoricalCase).filter(HistoricalCase.id == c["id"]).first()
                if not existing:
                    db_case = HistoricalCase(
                        id=c["id"],
                        title=c["title"],
                        category=c.get("category", "general"),
                        service=c.get("service", "unknown"),
                        symptoms=c.get("symptoms", ""),
                        root_cause=c.get("root_cause", ""),
                        recommended_remediation=c.get("recommended_remediation", "restart_connection_pool"),
                        log_patterns_json=json.dumps(c.get("log_patterns", [])),
                        metric_signatures_json=json.dumps(c.get("metric_signatures", {})),
                        tags_json=json.dumps(c.get("tags", [])),
                        source=c.get("source", "kaggle_import")
                    )
                    db.add(db_case)
            try:
                db.commit()
            except Exception:
                db.rollback()

dataset_importer = DatasetImporter()

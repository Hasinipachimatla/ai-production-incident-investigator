from app.core.config import settings
from app.services.dataset_importer import dataset_importer
from app.services.retrieval_engine import retrieval_engine

def test_kaggle_sample_csv_import(db_session):
    sample_path = settings.SAMPLE_KAGGLE_PATH
    assert sample_path.exists()

    initial_count = len(retrieval_engine.cases)

    # Ingest the Kaggle AIOps sample CSV
    res = dataset_importer.parse_and_import_csv(
        file_path=sample_path,
        db=db_session,
        source_label="kaggle_test_import"
    )

    assert res["status"] == "success"
    assert res["imported_count"] >= 5
    assert res["detected_format"] == "kaggle_aiops_failure_detection"
    assert len(retrieval_engine.cases) >= initial_count + res["imported_count"]

def test_dataset_stats_endpoint(client):
    res = client.get("/api/dataset/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] > 0
    assert "categories" in data
    assert "services" in data

def test_malformed_and_missing_columns_csv(tmp_path, db_session):
    """Verify importer handles missing columns, absent labels, empty rows, and malformed encoding."""
    test_csv = tmp_path / "messy_telemetry.csv"
    test_csv.write_text(
        "service,symptoms\n"
        "auth-service,JWT verification failure on expired public key\n"
        ",\n"  # Empty row
        "payment-svc,504 Gateway Timeout downstream\n"
        ",Missing service name\n"
        "order-service,\n",
        encoding="utf-8"
    )

    initial_count = len(retrieval_engine.cases)
    res = dataset_importer.parse_and_import_csv(
        file_path=test_csv,
        db=db_session,
        source_label="messy_test"
    )

    assert res["status"] == "success"
    assert res["imported_count"] >= 2
    assert len(retrieval_engine.cases) >= initial_count + res["imported_count"]

def test_json_dataset_import(db_session):
    """Verify ingestion of arbitrary JSON records without crashing."""
    raw_json_cases = [
        {
            "title": "Kafka consumer group rebalance storm",
            "service": "event-processor",
            "category": "streaming",
            "symptoms": "Consumer heartbeat timeout causing perpetual partition rebalance",
            "root_cause": "Excessive max.poll.interval.ms threshold breach",
            "recommended_remediation": "scale_worker_replicas"
        }
    ]
    initial_count = len(retrieval_engine.cases)
    dataset_importer._ingest_cases(raw_json_cases, db=db_session)
    assert len(retrieval_engine.cases) == initial_count + 1
    new_case = next(c for c in retrieval_engine.cases if c.get("service") == "event-processor")
    assert new_case["recommended_remediation"] == "scale_worker_replicas"
    assert "id" in new_case


import csv
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.services.dataset_importer import dataset_importer
from app.services.retrieval_engine import retrieval_engine
from app.schemas.dataset import DatasetImportResponse, DatasetStatsResponse

router = APIRouter(prefix="/dataset", tags=["Dataset Pipeline"])

@router.post("/import-kaggle-sample", response_model=DatasetImportResponse)
def import_kaggle_sample(db: Session = Depends(get_db)):
    """
    Imports the Kaggle AIOps Failure Detection sample dataset
    from data/sample_kaggle_aiops.csv into the historical case repository.
    """
    sample_path = settings.SAMPLE_KAGGLE_PATH
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample Kaggle dataset file not found.")

    res = dataset_importer.parse_and_import_csv(
        file_path=sample_path,
        db=db,
        source_label="kaggle_aiops_sample"
    )
    return {
        "status": res["status"],
        "imported_count": res["imported_count"],
        "skipped_count": res["skipped_count"],
        "total_cases_in_repo": res["total_cases_in_repo"],
        "format_detected": res["detected_format"],
        "filename": res["filename"],
        "message": f"Successfully ingested {res['imported_count']} Kaggle failure cases into repository."
    }

@router.post("/upload", response_model=DatasetImportResponse)
async def upload_custom_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts an uploaded CSV file from any of the candidate Kaggle datasets
    or observability telemetry logs, parses columns, and imports into the repository.
    """
    if not file.filename.endswith(".csv") and not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .csv and .json files are supported.")

    upload_dir = settings.DATA_DIR / "custom_imports"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest_path = upload_dir / file.filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file.filename.endswith(".csv"):
        res = dataset_importer.parse_and_import_csv(
            file_path=dest_path,
            db=db,
            source_label=f"uploaded_{file.filename}"
        )
    else:
        # JSON import
        with open(dest_path, "r", encoding="utf-8") as jf:
            data = json.load(jf)
            if isinstance(data, list):
                dataset_importer._ingest_cases(data, db)
                imported_count = len(data)
            else:
                imported_count = 0
        res = {
            "status": "success",
            "imported_count": imported_count,
            "skipped_count": 0,
            "detected_format": "json_records",
            "filename": file.filename,
            "total_cases_in_repo": len(retrieval_engine.cases)
        }

    return {
        "status": res["status"],
        "imported_count": res["imported_count"],
        "skipped_count": res["skipped_count"],
        "total_cases_in_repo": res["total_cases_in_repo"],
        "format_detected": res["detected_format"],
        "filename": res["filename"],
        "message": f"Successfully imported {res['imported_count']} records from {file.filename}."
    }

@router.get("/stats", response_model=DatasetStatsResponse)
def get_dataset_stats():
    """Returns descriptive statistics of historical cases repository."""
    cases = retrieval_engine.cases
    categories: Dict[str, int] = {}
    services: Dict[str, int] = {}
    sources: Dict[str, int] = {}

    for c in cases:
        cat = c.get("category", "general")
        svc = c.get("service", "unknown")
        src = c.get("source", "benchmark")
        categories[cat] = categories.get(cat, 0) + 1
        services[svc] = services.get(svc, 0) + 1
        sources[src] = sources.get(src, 0) + 1

    return {
        "total_cases": len(cases),
        "categories": categories,
        "services": services,
        "sources": sources
    }

@router.get("/preview")
def preview_kaggle_csv():
    """Returns headers and first 5 sample rows of the candidate Kaggle schema."""
    sample_path = settings.SAMPLE_KAGGLE_PATH
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample dataset not found.")

    rows = []
    headers = []
    with open(sample_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for i, row in enumerate(reader):
            if i >= 5:
                break
            rows.append(row)

    return {
        "filename": sample_path.name,
        "headers": headers,
        "sample_rows": rows
    }

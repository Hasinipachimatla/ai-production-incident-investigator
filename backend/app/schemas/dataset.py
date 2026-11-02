from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class DatasetRecordPreview(BaseModel):
    id: str
    title: str
    category: str
    service: str
    symptoms: str
    root_cause: str
    recommended_remediation: str
    source: str

class DatasetImportResponse(BaseModel):
    status: str
    imported_count: int
    skipped_count: int
    total_cases_in_repo: int
    format_detected: str
    filename: str
    message: str

class DatasetStatsResponse(BaseModel):
    total_cases: int
    categories: Dict[str, int]
    services: Dict[str, int]
    sources: Dict[str, int]

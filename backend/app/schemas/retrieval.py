from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class RetrievalCandidate(BaseModel):
    id: str
    title: str
    category: str
    service: str
    symptoms: str
    root_cause: str
    recommended_remediation: str
    similarity_score: float
    is_irrelevant: Optional[bool] = None
    matching_evidence: Optional[Dict[str, Any]] = None

class RetrievalResult(BaseModel):
    method: str  # "fixed_top_k" or "adaptive_threshold"
    k_applied: int
    threshold_applied: Optional[float] = None
    retrieved_count: int
    irrelevant_count: Optional[int] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    candidates: List[RetrievalCandidate]

class RetrievalCompareRequest(BaseModel):
    query_text: str
    service: Optional[str] = None
    top_k: int = 3
    threshold: float = 0.55
    ground_truth_case_ids: Optional[List[str]] = None

class ComparativeRetrievalResponse(BaseModel):
    query_text: str
    ground_truth_case_ids: Optional[List[str]] = None
    fixed_top_k: RetrievalResult
    adaptive: RetrievalResult
    analysis: str

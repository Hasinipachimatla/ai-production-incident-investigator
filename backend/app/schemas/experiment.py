from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class MethodEvalMetrics(BaseModel):
    mean_precision: float
    mean_recall: float
    mean_f1: float
    total_retrieved: int
    total_irrelevant: int
    avg_retrieved_per_query: float
    avg_irrelevant_per_query: float

class QueryEvalResult(BaseModel):
    query_id: str
    query_text: str
    service: Optional[str] = None
    ground_truth_count: int
    ground_truth_ids: List[str]
    
    # Baseline Top-K=3
    top_k_retrieved_ids: List[str]
    top_k_precision: float
    top_k_recall: float
    top_k_f1: float
    top_k_retrieved_count: int
    top_k_irrelevant_count: int
    
    # Adaptive Threshold
    adaptive_retrieved_ids: List[str]
    adaptive_precision: float
    adaptive_recall: float
    adaptive_f1: float
    adaptive_retrieved_count: int
    adaptive_irrelevant_count: int
    
    irrelevant_noise_reduction: int  # top_k_irrelevant - adaptive_irrelevant

class ExperimentRunRequest(BaseModel):
    threshold: Optional[float] = 0.55
    top_k: Optional[int] = 3

class ExperimentReport(BaseModel):
    experiment_id: str
    executed_at: str
    num_queries: int
    parameters: Dict[str, Any]
    baseline_top_k: MethodEvalMetrics
    adaptive_threshold: MethodEvalMetrics
    query_breakdown: List[QueryEvalResult]
    summary_findings: str

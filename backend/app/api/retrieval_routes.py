from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.retrieval_engine import retrieval_engine
from app.schemas.retrieval import RetrievalCompareRequest, ComparativeRetrievalResponse

router = APIRouter(prefix="/retrieval", tags=["Retrieval Engine"])

@router.post("/compare", response_model=ComparativeRetrievalResponse)
def compare_retrieval_methods(payload: RetrievalCompareRequest):
    """
    Executes identical query against historical cases using both
    Fixed Top-K (baseline) and Adaptive Threshold methods.
    Calculates precision, recall, F1, and irrelevant case count.
    """
    if not payload.query_text or not payload.query_text.strip():
        raise HTTPException(status_code=400, detail="query_text cannot be empty.")

    res = retrieval_engine.compare_methods(
        query_text=payload.query_text,
        threshold=payload.threshold,
        top_k=payload.top_k,
        service_hint=payload.service,
        ground_truth_ids=payload.ground_truth_case_ids
    )
    return res

@router.get("/historical-cases")
def list_historical_cases():
    """Lists all historical incident cases currently loaded in the repository."""
    return {
        "total_cases": len(retrieval_engine.cases),
        "cases": retrieval_engine.cases
    }

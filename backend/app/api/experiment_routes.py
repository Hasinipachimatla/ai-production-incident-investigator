import json
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services.experiment_runner import experiment_runner
from app.schemas.experiment import ExperimentRunRequest, ExperimentReport

router = APIRouter(prefix="/experiments", tags=["Evaluation Experiments"])

@router.post("/run", response_model=ExperimentReport)
def run_experiment(payload: ExperimentRunRequest = None):
    """
    Executes offline comparative evaluation comparing baseline Top-K=3
    vs Adaptive Relevance-Threshold retrieval on labeled benchmark dataset.
    Calculates actual precision, recall, F1, retrieval counts, and noise reduction.
    """
    thresh = payload.threshold if payload and payload.threshold is not None else 0.55
    k = payload.top_k if payload and payload.top_k is not None else 3

    try:
        report = experiment_runner.run_benchmark_experiment(threshold=thresh, top_k=k)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment execution failed: {str(e)}")

@router.get("/last-results")
def get_last_results():
    """Returns the most recent persisted experiment results."""
    results_file = settings.DATA_DIR / "last_experiment_results.json"
    if results_file.exists():
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read results: {str(e)}")
    
    # If no run has been saved yet, execute one on-the-fly!
    return experiment_runner.run_benchmark_experiment()

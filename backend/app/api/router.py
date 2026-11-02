from fastapi import APIRouter
from app.api.fault_routes import router as fault_router
from app.api.telemetry_routes import router as telemetry_router
from app.api.incident_routes import router as incident_router
from app.api.retrieval_routes import router as retrieval_router
from app.api.remediation_routes import router as remediation_router
from app.api.experiment_routes import router as experiment_router
from app.api.dataset_routes import router as dataset_router
from app.api.shopease_routes import router as shopease_router

api_router = APIRouter(prefix="/api")

api_router.include_router(fault_router)
api_router.include_router(telemetry_router)
api_router.include_router(incident_router)
api_router.include_router(retrieval_router)
api_router.include_router(remediation_router)
api_router.include_router(experiment_router)
api_router.include_router(dataset_router)
api_router.include_router(shopease_router)

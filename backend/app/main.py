import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, ensure_migrations
from app.models.historical_case import HistoricalCase
from app.services.retrieval_engine import retrieval_engine
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Database Tables and apply schema migrations
    Base.metadata.create_all(bind=engine)
    ensure_migrations()

    # 2. Seed Initial Historical Incidents from data/historical_incidents.json
    db = SessionLocal()
    try:
        if settings.HISTORICAL_INCIDENTS_PATH.exists():
            with open(settings.HISTORICAL_INCIDENTS_PATH, "r", encoding="utf-8") as f:
                cases = json.load(f)

            # Populate database if empty
            existing_count = db.query(HistoricalCase).count()
            if existing_count == 0:
                for c in cases:
                    db_case = HistoricalCase(
                        id=c["id"],
                        title=c["title"],
                        category=c.get("category", "general"),
                        service=c.get("service", "unknown"),
                        symptoms=c.get("symptoms", ""),
                        root_cause=c.get("root_cause", ""),
                        recommended_remediation=c.get("recommended_remediation", ""),
                        log_patterns_json=json.dumps(c.get("log_patterns", [])),
                        metric_signatures_json=json.dumps(c.get("metric_signatures", {})),
                        tags_json=json.dumps(c.get("tags", [])),
                        source="curated_benchmark"
                    )
                    db.add(db_case)
                db.commit()

            # Load into retrieval vector engine
            retrieval_engine.load_cases(cases)
            print(f"[Startup] Loaded {len(cases)} historical incident cases into Retrieval Engine.")
    finally:
        db.close()

    # 3. Start Autonomous Background Monitoring Daemon
    from app.services.monitoring_service import monitoring_service
    if settings.ENABLE_BACKGROUND_MONITORING:
        monitoring_service.start()

    yield
    print("[Shutdown] Production Incident Investigator shutting down.")
    if settings.ENABLE_BACKGROUND_MONITORING:
        monitoring_service.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Research platform for Adaptive Incident Retrieval and Controlled Closed-Loop Remediation.",
    lifespan=lifespan
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "research_modules": {
            "adaptive_retrieval": "/api/retrieval/compare",
            "closed_loop_remediation": "/api/remediation/allowlist",
            "fault_simulator": "/api/faults/catalog",
            "offline_evaluation": "/api/experiments/run",
            "kaggle_dataset_pipeline": "/api/dataset/stats"
        }
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "retrieval_engine_cases": len(retrieval_engine.cases),
        "engine_fitted": retrieval_engine.is_fitted
    }

import json
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.services.retrieval_engine import retrieval_engine
from app.models.historical_case import HistoricalCase
from app.models.incident import Incident
from app.models.audit_log import IncidentAuditLog

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    # Ensure test isolation by resetting dynamic tables
    session.query(IncidentAuditLog).delete()
    session.query(Incident).delete()
    session.commit()

    # Load historical cases from data file
    if settings.HISTORICAL_INCIDENTS_PATH.exists():
        with open(settings.HISTORICAL_INCIDENTS_PATH, "r", encoding="utf-8") as f:
            cases = json.load(f)
            retrieval_engine.load_cases(cases)

    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

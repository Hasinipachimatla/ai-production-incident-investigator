from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_migrations():
    """Ensure SQLite schema has required columns without requiring alembic."""
    try:
        with engine.connect() as conn:
            # Check if incidents table exists
            res = conn.execute(Base.metadata.tables["incidents"].select().limit(0)) if "incidents" in Base.metadata.tables else None
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(incidents)")).fetchall()]
            if cols and "target_system" not in cols:
                conn.execute(text("ALTER TABLE incidents ADD COLUMN target_system VARCHAR(64) DEFAULT 'simulator'"))
                conn.commit()
            if cols and "confidence_explanation" not in cols:
                conn.execute(text("ALTER TABLE incidents ADD COLUMN confidence_explanation TEXT DEFAULT ''"))
                conn.commit()
    except Exception:
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.core.database import Base

class HistoricalCase(Base):
    __tablename__ = "historical_cases"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    service = Column(String(128), nullable=False, index=True)
    symptoms = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    recommended_remediation = Column(String(64), nullable=False)
    log_patterns_json = Column(Text, default="[]")
    metric_signatures_json = Column(Text, default="{}")
    tags_json = Column(Text, default="[]")
    source = Column(String(64), default="curated_benchmark")
    created_at = Column(DateTime, default=datetime.utcnow)

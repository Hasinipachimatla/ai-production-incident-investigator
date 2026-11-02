from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base

class IncidentAuditLog(Base):
    __tablename__ = "incident_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), nullable=False, index=True)
    stage = Column(String(64), nullable=False)
    action_taken = Column(String(128), nullable=False)
    details = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)

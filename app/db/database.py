import os
from sqlalchemy import create_engine, Column, String, Float, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, sessionmaker
from app.domain.models import SessionStatus

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://volt:secret@db:5432/sessions")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SessionRecord(Base):
    """ORM-model – kortlægger ChargingSession til database-tabel"""
    __tablename__ = "charging_sessions"

    session_id   = Column(PGUUID(as_uuid=True), primary_key=True)
    charger_id   = Column(String(64), nullable=False)
    connector_id = Column(String(64), nullable=False)
    user_id      = Column(String(64), nullable=False)
    status       = Column(SAEnum(SessionStatus), nullable=False, default=SessionStatus.INITIATED)
    started_at   = Column(DateTime, nullable=True)
    ended_at     = Column(DateTime, nullable=True)
    energy_kwh   = Column(Float, nullable=True)
    cost_dkk     = Column(Float, nullable=True)
    tariff_rate  = Column(Float, nullable=True)
    created_at   = Column(DateTime, nullable=False)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

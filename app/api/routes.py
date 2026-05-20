import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.repositories import SessionRepository
from app.domain.models import ChargingSession, SessionStatus
from app.metrics import SESSION_EVENTS_TOTAL
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Charging Sessions"])

API_KEY = os.getenv("API_KEY", "dev-secret-key")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    charger_id: str
    connector_id: str
    user_id: str


class EndSessionRequest(BaseModel):
    energy_kwh: float
    tariff_rate: float


class SessionResponse(BaseModel):
    session_id: str
    charger_id: str
    connector_id: str
    user_id: str
    status: str
    started_at: str | None
    ended_at: str | None
    energy_kwh: float | None
    cost_dkk: float | None
    tariff_rate: float | None


def _format(session: ChargingSession) -> SessionResponse:
    return SessionResponse(
        session_id=str(session.session_id),
        charger_id=session.charger_id,
        connector_id=session.connector_id,
        user_id=session.user_id,
        status=session.status.value,
        started_at=session.started_at.isoformat() if session.started_at else None,
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        energy_kwh=session.energy_delivered.kwh if session.energy_delivered else None,
        cost_dkk=session.session_cost.amount_dkk if session.session_cost else None,
        tariff_rate=session.session_cost.tariff_rate if session.session_cost else None,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=SessionResponse, status_code=201, dependencies=[Depends(verify_api_key)])
def create_session(body: CreateSessionRequest, db: Session = Depends(get_db)):
    """Opret ny session (INITIATED)"""
    session = ChargingSession(
        charger_id=body.charger_id,
        connector_id=body.connector_id,
        user_id=body.user_id,
    )
    repo = SessionRepository(db)
    repo.save(session)
    SESSION_EVENTS_TOTAL.labels(event="created").inc()
    logger.info("Session created: %s", session.session_id)
    return _format(session)


@router.post("/{session_id}/start", response_model=SessionResponse, dependencies=[Depends(verify_api_key)])
def start_session(session_id: UUID, db: Session = Depends(get_db)):
    """Start session (INITIATED → ACTIVE)"""
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        session.start()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    repo.save(session)
    SESSION_EVENTS_TOTAL.labels(event="started").inc()
    logger.info("Session started: %s", session_id)
    return _format(session)


@router.post("/{session_id}/end", response_model=SessionResponse, dependencies=[Depends(verify_api_key)])
def end_session(session_id: UUID, body: EndSessionRequest, db: Session = Depends(get_db)):
    """Afslut session (ACTIVE → COMPLETED) og beregn pris"""
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        session.end(body.energy_kwh, body.tariff_rate)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    repo.save(session)
    SESSION_EVENTS_TOTAL.labels(event="completed").inc()
    logger.info("Session completed: %s – %.2f DKK", session_id, session.session_cost.amount_dkk)
    return _format(session)


@router.get("/stats/summary")
def get_summary(db: Session = Depends(get_db)):
    """Aggregeret statistik til BI-dashboard"""
    return SessionRepository(db).get_summary()


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    """Hent én session med alle detaljer"""
    session = SessionRepository(db).get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _format(session)


@router.get("/", response_model=list[SessionResponse])
def list_sessions(status: str | None = None, db: Session = Depends(get_db)):
    """List alle sessioner – filtrer evt. på status"""
    filter_status = SessionStatus(status) if status else None
    sessions = SessionRepository(db).get_all(filter_status)
    return [_format(s) for s in sessions]

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import SessionRecord
from app.domain.models import ChargingSession, EnergyDelivered, SessionCost, SessionStatus


def _to_domain(record: SessionRecord) -> ChargingSession:
    session = ChargingSession(
        charger_id=record.charger_id,
        connector_id=record.connector_id,
        user_id=record.user_id,
        session_id=record.session_id,
        status=record.status,
        started_at=record.started_at,
        ended_at=record.ended_at,
        created_at=record.created_at,
    )
    if record.energy_kwh is not None:
        session.energy_delivered = EnergyDelivered(record.energy_kwh)
    if record.cost_dkk is not None:
        session.session_cost = SessionCost(record.cost_dkk, record.tariff_rate)
    return session


def _to_record(session: ChargingSession) -> SessionRecord:
    return SessionRecord(
        session_id=session.session_id,
        charger_id=session.charger_id,
        connector_id=session.connector_id,
        user_id=session.user_id,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        energy_kwh=session.energy_delivered.kwh if session.energy_delivered else None,
        cost_dkk=session.session_cost.amount_dkk if session.session_cost else None,
        tariff_rate=session.session_cost.tariff_rate if session.session_cost else None,
        created_at=session.created_at,
    )


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, session: ChargingSession) -> ChargingSession:
        existing = self.db.query(SessionRecord).filter_by(session_id=session.session_id).first()
        if existing:
            existing.status = session.status
            existing.started_at = session.started_at
            existing.ended_at = session.ended_at
            existing.energy_kwh = session.energy_delivered.kwh if session.energy_delivered else None
            existing.cost_dkk = session.session_cost.amount_dkk if session.session_cost else None
            existing.tariff_rate = session.session_cost.tariff_rate if session.session_cost else None
        else:
            self.db.add(_to_record(session))
        self.db.commit()
        return session

    def get_by_id(self, session_id: UUID) -> ChargingSession | None:
        record = self.db.query(SessionRecord).filter_by(session_id=session_id).first()
        return _to_domain(record) if record else None

    def get_all(self, status: SessionStatus | None = None) -> list[ChargingSession]:
        query = self.db.query(SessionRecord)
        if status:
            query = query.filter_by(status=status)
        return [_to_domain(r) for r in query.order_by(SessionRecord.created_at.desc()).all()]

    def get_summary(self) -> dict:
        total = self.db.query(func.count(SessionRecord.session_id)).scalar()
        completed = self.db.query(func.count(SessionRecord.session_id)).filter_by(status=SessionStatus.COMPLETED).scalar()
        faulted = self.db.query(func.count(SessionRecord.session_id)).filter_by(status=SessionStatus.FAULTED).scalar()
        total_kwh = self.db.query(func.sum(SessionRecord.energy_kwh)).scalar() or 0
        total_dkk = self.db.query(func.sum(SessionRecord.cost_dkk)).scalar() or 0
        avg_dkk = self.db.query(func.avg(SessionRecord.cost_dkk)).scalar() or 0
        return {
            "total_sessions": total,
            "completed_sessions": completed,
            "faulted_sessions": faulted,
            "total_energy_kwh": round(total_kwh, 2),
            "total_revenue_dkk": round(total_dkk, 2),
            "avg_session_cost_dkk": round(avg_dkk, 2),
        }

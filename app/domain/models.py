from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4


class SessionStatus(str, Enum):
    INITIATED = "INITIATED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAULTED = "FAULTED"


@dataclass(frozen=True)
class EnergyDelivered:
    """Value Object – immutabel repræsentation af leveret energi i kWh"""
    kwh: float

    def __post_init__(self):
        if self.kwh < 0:
            raise ValueError("EnergyDelivered cannot be negative")


@dataclass(frozen=True)
class SessionCost:
    """Value Object – immutabel beregnet sessionspris i DKK"""
    amount_dkk: float
    tariff_rate: float


@dataclass
class ChargingSession:
    """
    Aggregate Root – styrer sessionens livscyklus og håndhæver invarianter.
    En ChargingSession repræsenterer én komplet lade-hændelse fra start til slut.
    """
    charger_id: str
    connector_id: str
    user_id: str
    session_id: UUID = field(default_factory=uuid4)
    status: SessionStatus = SessionStatus.INITIATED
    started_at: datetime | None = None
    ended_at: datetime | None = None
    energy_delivered: EnergyDelivered | None = None
    session_cost: SessionCost | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def start(self) -> None:
        """Start sessionen – kun muligt fra INITIATED"""
        if self.status != SessionStatus.INITIATED:
            raise ValueError(f"Cannot start session with status {self.status}")
        self.status = SessionStatus.ACTIVE
        self.started_at = datetime.utcnow()

    def end(self, kwh: float, tariff_rate: float) -> None:
        """Afslut sessionen og beregn pris – kun muligt fra ACTIVE"""
        if self.status != SessionStatus.ACTIVE:
            raise ValueError(f"Cannot end session with status {self.status}")
        self.energy_delivered = EnergyDelivered(kwh)
        self.session_cost = SessionCost(
            amount_dkk=round(kwh * tariff_rate, 2),
            tariff_rate=tariff_rate,
        )
        self.status = SessionStatus.COMPLETED
        self.ended_at = datetime.utcnow()

    def fault(self, reason: str = "") -> None:
        """Marker sessionen som fejlet"""
        self.status = SessionStatus.FAULTED
        self.ended_at = datetime.utcnow()

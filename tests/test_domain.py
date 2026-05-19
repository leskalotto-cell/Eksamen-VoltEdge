import pytest
from app.domain.models import ChargingSession, EnergyDelivered, SessionCost, SessionStatus
from app.domain.services import PricingService


# ── EnergyDelivered ───────────────────────────────────────────────────────────

def test_energy_delivered_valid():
    e = EnergyDelivered(kwh=25.5)
    assert e.kwh == 25.5

def test_energy_delivered_zero_is_valid():
    e = EnergyDelivered(kwh=0)
    assert e.kwh == 0

def test_energy_delivered_negative_raises():
    with pytest.raises(ValueError):
        EnergyDelivered(kwh=-1)

def test_energy_delivered_is_immutable():
    e = EnergyDelivered(kwh=10)
    with pytest.raises(Exception):
        e.kwh = 20


# ── PricingService ────────────────────────────────────────────────────────────

def test_pricing_service_calculates_correctly():
    service = PricingService()
    energy = EnergyDelivered(kwh=10.0)
    cost = service.calculate(energy, tariff_rate=2.50)
    assert cost.amount_dkk == 25.00
    assert cost.tariff_rate == 2.50

def test_pricing_service_rounds_to_two_decimals():
    service = PricingService()
    cost = service.calculate(EnergyDelivered(kwh=1/3), tariff_rate=1.0)
    assert len(str(cost.amount_dkk).split(".")[-1]) <= 2

def test_pricing_service_zero_tariff_raises():
    service = PricingService()
    with pytest.raises(ValueError):
        service.calculate(EnergyDelivered(kwh=10), tariff_rate=0)

def test_pricing_service_negative_tariff_raises():
    service = PricingService()
    with pytest.raises(ValueError):
        service.calculate(EnergyDelivered(kwh=10), tariff_rate=-1)


# ── ChargingSession lifecycle ─────────────────────────────────────────────────

def make_session():
    return ChargingSession(charger_id="CHG-01", connector_id="CON-1", user_id="USR-42")

def test_session_initial_status():
    s = make_session()
    assert s.status == SessionStatus.INITIATED

def test_session_start():
    s = make_session()
    s.start()
    assert s.status == SessionStatus.ACTIVE
    assert s.started_at is not None

def test_session_start_twice_raises():
    s = make_session()
    s.start()
    with pytest.raises(ValueError):
        s.start()

def test_session_end():
    s = make_session()
    s.start()
    s.end(kwh=20.0, tariff_rate=2.0)
    assert s.status == SessionStatus.COMPLETED
    assert s.energy_delivered.kwh == 20.0
    assert s.session_cost.amount_dkk == 40.0
    assert s.ended_at is not None

def test_session_end_without_start_raises():
    s = make_session()
    with pytest.raises(ValueError):
        s.end(kwh=10.0, tariff_rate=2.0)

def test_session_fault():
    s = make_session()
    s.start()
    s.fault()
    assert s.status == SessionStatus.FAULTED
    assert s.ended_at is not None

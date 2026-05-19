import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Sæt test-database før app importeres
os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL", "postgresql://volt:secret@localhost:5432/sessions"
)
os.environ["API_KEY"] = "test-key"

from app.main import app
from app.db.database import Base, get_db, engine

# Opret tabeller og brug test-database
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
HEADERS = {"x-api-key": "test-key"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_session():
    r = client.post("/sessions/", json={
        "charger_id": "CHG-01",
        "connector_id": "CON-1",
        "user_id": "USR-42"
    }, headers=HEADERS)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "INITIATED"
    assert data["charger_id"] == "CHG-01"
    return data["session_id"]


def test_create_session_missing_api_key():
    r = client.post("/sessions/", json={
        "charger_id": "CHG-01", "connector_id": "CON-1", "user_id": "USR-42"
    })
    assert r.status_code == 422  # Missing header


def test_full_session_lifecycle():
    # 1. Opret
    r = client.post("/sessions/", json={
        "charger_id": "CHG-02", "connector_id": "CON-2", "user_id": "USR-99"
    }, headers=HEADERS)
    assert r.status_code == 201
    sid = r.json()["session_id"]

    # 2. Start
    r = client.post(f"/sessions/{sid}/start", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "ACTIVE"

    # 3. Afslut
    r = client.post(f"/sessions/{sid}/end", json={
        "energy_kwh": 15.0, "tariff_rate": 2.50
    }, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "COMPLETED"
    assert data["energy_kwh"] == 15.0
    assert data["cost_dkk"] == 37.50

    # 4. Hent
    r = client.get(f"/sessions/{sid}")
    assert r.status_code == 200
    assert r.json()["cost_dkk"] == 37.50


def test_start_already_active_returns_409():
    r = client.post("/sessions/", json={
        "charger_id": "CHG-03", "connector_id": "CON-3", "user_id": "USR-01"
    }, headers=HEADERS)
    sid = r.json()["session_id"]
    client.post(f"/sessions/{sid}/start", headers=HEADERS)
    r = client.post(f"/sessions/{sid}/start", headers=HEADERS)
    assert r.status_code == 409


def test_get_nonexistent_session_returns_404():
    import uuid
    r = client.get(f"/sessions/{uuid.uuid4()}")
    assert r.status_code == 404


def test_list_sessions():
    r = client.get("/sessions/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_stats_summary():
    r = client.get("/sessions/stats/summary")
    assert r.status_code == 200
    data = r.json()
    assert "total_sessions" in data
    assert "total_revenue_dkk" in data

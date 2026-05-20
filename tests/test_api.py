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


def test_metrics_endpoint():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "voltedge_request_count" in r.text


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


def test_stats_summary_has_all_dashboard_fields():
    r = client.get("/sessions/stats/summary")
    assert r.status_code == 200
    data = r.json()

    expected_keys = {
        "total_sessions",
        "completed_sessions",
        "faulted_sessions",
        "total_energy_kwh",
        "total_revenue_dkk",
        "avg_session_cost_dkk",
    }

    assert expected_keys == set(data.keys())
    assert isinstance(data["total_sessions"], int)
    assert isinstance(data["completed_sessions"], int)
    assert isinstance(data["faulted_sessions"], int)
    assert isinstance(data["total_energy_kwh"], float)
    assert isinstance(data["total_revenue_dkk"], float)
    assert isinstance(data["avg_session_cost_dkk"], float)
    assert data["total_sessions"] >= 0
    assert data["completed_sessions"] >= 0
    assert data["faulted_sessions"] >= 0
    assert data["total_energy_kwh"] >= 0.0
    assert data["total_revenue_dkk"] >= 0.0
    assert data["avg_session_cost_dkk"] >= 0.0


def test_stats_summary_counts_all_registered_sessions():
    summary_before = client.get("/sessions/stats/summary")
    assert summary_before.status_code == 200
    before_data = summary_before.json()

    created_ids = []
    for i in range(3):
        r = client.post("/sessions/", json={
            "charger_id": f"CHG-REG-{i}",
            "connector_id": f"CON-{i}",
            "user_id": f"USR-{i}",
        }, headers=HEADERS)
        assert r.status_code == 201
        created_ids.append(r.json()["session_id"])

    r = client.post(f"/sessions/{created_ids[0]}/start", headers=HEADERS)
    assert r.status_code == 200
    r = client.post(f"/sessions/{created_ids[0]}/end", json={
        "energy_kwh": 18.5,
        "tariff_rate": 2.25,
    }, headers=HEADERS)
    assert r.status_code == 200

    summary_after = client.get("/sessions/stats/summary")
    assert summary_after.status_code == 200
    after_data = summary_after.json()

    assert after_data["total_sessions"] == before_data["total_sessions"] + 3
    assert after_data["completed_sessions"] == before_data["completed_sessions"] + 1
    assert after_data["total_energy_kwh"] >= before_data["total_energy_kwh"]
    assert after_data["total_revenue_dkk"] >= before_data["total_revenue_dkk"]

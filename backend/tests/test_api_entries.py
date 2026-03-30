import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.dependencies import get_db
from backend.api.main import app
from backend.db.database import Base


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _base_entry(date="2026-03-27", **overrides):
    """Minimal valid entry payload with all required fields."""
    payload = {
        "date": date,
        "stretching": True,
        "alcohol": False,
        "heavy_dinner": False,
        "omega3": True,
        "vitamin_d": True,
        "magnesium": True,
        "turmeric": False,
        "mood_score": 6,
        "pain_records": [{"location": "lumbar", "intensity": 5}],
    }
    payload.update(overrides)
    return payload


def test_create_entry(client):
    response = client.post(
        "/api/entries",
        json=_base_entry(
            pain_records=[{"location": "lumbar", "intensity": 6, "pattern": "constante"}],
            medication_records=[
                {"name": "Ibuprofen", "dose": "75mg", "time_taken": "08:00", "effectiveness": 7}
            ],
            mood_emotions=["cansancio"],
        ),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["date"] == "2026-03-27"
    assert data["stretching"] is True
    assert data["mood_score"] == 6
    assert data["alcohol"] is False
    assert data["omega3"] is True
    assert len(data["pain_records"]) == 1
    assert data["pain_records"][0]["location"] == "lumbar"
    assert data["pain_records"][0]["intensity"] == 6


def test_create_entry_duplicate_date_updates(client):
    client.post("/api/entries", json=_base_entry())
    response = client.post(
        "/api/entries",
        json=_base_entry(
            stretching=False,
            mood_score=7,
            alcohol=True,
            pain_records=[{"location": "lumbar", "intensity": 4}],
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stretching"] is False
    assert data["mood_score"] == 7
    assert data["alcohol"] is True
    assert data["pain_records"][0]["intensity"] == 4


def test_create_entry_missing_mood_score_fails(client):
    payload = _base_entry()
    del payload["mood_score"]
    response = client.post("/api/entries", json=payload)
    assert response.status_code == 422


def test_create_entry_missing_habits_fails(client):
    payload = _base_entry()
    del payload["alcohol"]
    response = client.post("/api/entries", json=payload)
    assert response.status_code == 422


def test_get_entry_by_date(client):
    client.post("/api/entries", json=_base_entry())
    response = client.get("/api/entries/2026-03-27")
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-03-27"
    assert data["mood_score"] == 6
    assert data["stretching"] is True
    # Verify eliminated record lists are NOT in response
    assert "mood_records" not in data
    assert "stress_records" not in data
    assert "activity_records" not in data
    assert "nutrition_records" not in data


def test_get_entry_not_found(client):
    response = client.get("/api/entries/2026-01-01")
    assert response.status_code == 404


def test_list_entries(client):
    client.post("/api/entries", json=_base_entry("2026-03-25", mood_score=4))
    client.post("/api/entries", json=_base_entry("2026-03-26", mood_score=5))
    client.post("/api/entries", json=_base_entry("2026-03-27", mood_score=7))
    response = client.get("/api/entries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["date"] == "2026-03-27"


def test_list_entries_with_date_range(client):
    client.post("/api/entries", json=_base_entry("2026-03-25"))
    client.post("/api/entries", json=_base_entry("2026-03-26"))
    client.post("/api/entries", json=_base_entry("2026-03-27"))
    response = client.get("/api/entries?start_date=2026-03-26&end_date=2026-03-27")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_entry(client):
    client.post("/api/entries", json=_base_entry())
    response = client.delete("/api/entries/2026-03-27")
    assert response.status_code == 204
    response = client.get("/api/entries/2026-03-27")
    assert response.status_code == 404

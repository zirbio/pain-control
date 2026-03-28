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


def test_create_entry(client):
    response = client.post(
        "/api/entries",
        json={
            "date": "2026-03-27",
            "pain_records": [{"location": "lumbar", "intensity": 6, "pattern": "constante"}],
            "medication_records": [
                {"name": "Ibuprofen", "dose": "75mg", "time_taken": "08:00", "effectiveness": 7}
            ],
            "mood_records": [{"score": 6}],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["date"] == "2026-03-27"
    assert len(data["pain_records"]) == 1
    assert data["pain_records"][0]["location"] == "lumbar"
    assert data["pain_records"][0]["intensity"] == 6


def test_create_entry_duplicate_date_updates(client):
    client.post(
        "/api/entries",
        json={
            "date": "2026-03-27",
            "pain_records": [{"location": "lumbar", "intensity": 6}],
        },
    )
    response = client.post(
        "/api/entries",
        json={
            "date": "2026-03-27",
            "pain_records": [{"location": "lumbar", "intensity": 4}],
            "mood_records": [{"score": 7}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pain_records"][0]["intensity"] == 4
    assert len(data["mood_records"]) == 1


def test_get_entry_by_date(client):
    client.post(
        "/api/entries",
        json={
            "date": "2026-03-27",
            "pain_records": [{"location": "lumbar", "intensity": 5}],
        },
    )
    response = client.get("/api/entries/2026-03-27")
    assert response.status_code == 200
    assert response.json()["date"] == "2026-03-27"


def test_get_entry_not_found(client):
    response = client.get("/api/entries/2026-01-01")
    assert response.status_code == 404


def test_list_entries(client):
    client.post(
        "/api/entries",
        json={"date": "2026-03-25", "pain_records": [{"location": "lumbar", "intensity": 3}]},
    )
    client.post(
        "/api/entries",
        json={"date": "2026-03-26", "pain_records": [{"location": "lumbar", "intensity": 5}]},
    )
    client.post(
        "/api/entries",
        json={"date": "2026-03-27", "pain_records": [{"location": "lumbar", "intensity": 7}]},
    )
    response = client.get("/api/entries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["date"] == "2026-03-27"


def test_list_entries_with_date_range(client):
    client.post(
        "/api/entries",
        json={"date": "2026-03-25", "pain_records": [{"location": "lumbar", "intensity": 3}]},
    )
    client.post(
        "/api/entries",
        json={"date": "2026-03-26", "pain_records": [{"location": "lumbar", "intensity": 5}]},
    )
    client.post(
        "/api/entries",
        json={"date": "2026-03-27", "pain_records": [{"location": "lumbar", "intensity": 7}]},
    )
    response = client.get("/api/entries?start_date=2026-03-26&end_date=2026-03-27")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_entry(client):
    client.post(
        "/api/entries",
        json={"date": "2026-03-27", "pain_records": [{"location": "lumbar", "intensity": 5}]},
    )
    response = client.delete("/api/entries/2026-03-27")
    assert response.status_code == 204
    response = client.get("/api/entries/2026-03-27")
    assert response.status_code == 404

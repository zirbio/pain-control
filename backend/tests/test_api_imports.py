import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.dependencies import get_db
from backend.api.main import app
from backend.db.database import Base

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def client_with_imports(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    imports_dir = tmp_path / "imports"
    imports_dir.mkdir()
    shutil.copy(FIXTURES_DIR / "sample_health_export.xml", imports_dir / "export.xml")

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("backend.api.routers.imports.get_imports_dir", lambda: str(imports_dir))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_import_apple_health(client_with_imports):
    response = client_with_imports.post("/api/imports/apple-health")
    assert response.status_code == 200
    data = response.json()
    assert data["files_processed"] == 1
    assert data["days_imported"] >= 1


def test_import_with_missing_directory(tmp_path, monkeypatch):
    """Import endpoint returns structured error when imports dir doesn't exist."""
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
    monkeypatch.setattr(
        "backend.api.routers.imports.get_imports_dir", lambda: str(tmp_path / "nonexistent")
    )
    client = TestClient(app)
    response = client.post("/api/imports/apple-health")
    assert response.status_code == 200
    data = response.json()
    assert data["files_processed"] == 0
    assert "imports directory not found" in data["errors"][0]
    app.dependency_overrides.clear()


@pytest.fixture()
def client_with_csv_imports(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    imports_dir = tmp_path / "imports"
    imports_dir.mkdir()

    # Health + nutrition CSV (column names must match AppleHealthImporter.CSV_COLUMNS)
    csv_content = (
        "Fecha/Hora,Energía Activa (kJ),Frecuencia Cardiaca en Reposo (bpm),"
        "Variabilidad de Frecuencia Cardíaca (ms),Proteína (g),Cafeína (mg)\n"
        "2026-03-25 00:00,1200,62,45.3,120.5,250.0\n"
        "2026-03-26 00:00,1100,65,42.1,98.2,180.0\n"
    )
    (imports_dir / "HealthAutoExport-2026-03-25-2026-03-26.csv").write_text(csv_content)

    # Workouts CSV (column names match AppleHealthImporter.parse_workouts_csv)
    workout_content = (
        "Workout Type,Start,End,Duration,"
        "Energía Activa (kJ),"
        "Frecuencia Cardíaca Máxima (bpm),"
        "Frecuencia Cardíaca Promedio (bpm),"
        "Distancia (km),Conteo de Pasos\n"
        "Caminata al Aire Libre,2026-03-25 09:04,2026-03-25 09:36,00:32:15,"
        "450,135,105,2.5,3200\n"
    )
    (imports_dir / "Workouts-2026-03-01-2026-03-26.csv").write_text(workout_content)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("backend.api.routers.imports.get_imports_dir", lambda: str(imports_dir))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_import_csv_and_workouts(client_with_csv_imports):
    """CSV health+nutrition data and workouts are imported correctly."""
    response = client_with_csv_imports.post("/api/imports/apple-health")
    assert response.status_code == 200
    data = response.json()
    assert data["days_imported"] >= 2
    assert data["workouts_imported"] >= 1

    # Verify nutrition import records via entries API
    entries_resp = client_with_csv_imports.get("/api/entries")
    entries = entries_resp.json()
    assert len(entries) >= 2

    # Find the entry with nutrition data
    entry_with_nutrition = next(
        (e for e in entries if len(e["nutrition_import_records"]) > 0), None
    )
    assert entry_with_nutrition is not None
    ni = entry_with_nutrition["nutrition_import_records"][0]
    assert ni["protein_g"] is not None
    assert ni["caffeine_mg"] is not None

    # Find entry with workout
    entry_with_workout = next((e for e in entries if len(e["workout_records"]) > 0), None)
    assert entry_with_workout is not None
    w = entry_with_workout["workout_records"][0]
    assert w["workout_type"] == "Caminata al Aire Libre"
    assert w["max_hr"] == 135


def test_import_csv_idempotent(client_with_csv_imports):
    """Running CSV import twice produces same result, not duplicates."""
    resp1 = client_with_csv_imports.post("/api/imports/apple-health")
    days1 = resp1.json()["days_imported"]
    workouts1 = resp1.json()["workouts_imported"]

    resp2 = client_with_csv_imports.post("/api/imports/apple-health")
    days2 = resp2.json()["days_imported"]
    workouts2 = resp2.json()["workouts_imported"]

    assert days1 == days2
    assert workouts1 == workouts2


def test_import_idempotent(client_with_imports):
    """Running import twice with same XML produces same result, not duplicates."""
    response1 = client_with_imports.post("/api/imports/apple-health")
    days1 = response1.json()["days_imported"]

    response2 = client_with_imports.post("/api/imports/apple-health")
    days2 = response2.json()["days_imported"]

    assert days1 == days2  # Same count, not doubled


@pytest.fixture()
def client_with_healthmetrics_csv(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    imports_dir = tmp_path / "imports"
    imports_dir.mkdir()

    csv_content = (
        "Fecha/Hora,Energía Activa (kJ),Frecuencia Cardiaca en Reposo (bpm),"
        "Variabilidad de Frecuencia Cardíaca (ms)\n"
        "2026-03-28 00:00,1300,58,48.7\n"
    )
    (imports_dir / "HealthMetrics-2026-03-28.csv").write_text(csv_content)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("backend.api.routers.imports.get_imports_dir", lambda: str(imports_dir))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_import_healthmetrics_csv(client_with_healthmetrics_csv):
    """HealthMetrics-*.csv files (Health Auto Export naming) are imported."""
    response = client_with_healthmetrics_csv.post("/api/imports/apple-health")
    assert response.status_code == 200
    data = response.json()
    assert data["files_processed"] == 1
    assert data["days_imported"] == 1

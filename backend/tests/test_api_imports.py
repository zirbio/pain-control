import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.api.dependencies import get_db
from backend.api.main import app


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
    monkeypatch.setattr("backend.api.routers.imports.get_imports_dir", lambda: str(tmp_path / "nonexistent"))
    client = TestClient(app)
    response = client.post("/api/imports/apple-health")
    assert response.status_code == 200
    data = response.json()
    assert data["files_processed"] == 0
    assert "imports directory not found" in data["errors"][0]
    app.dependency_overrides.clear()


def test_import_idempotent(client_with_imports):
    """Running import twice with same XML produces same result, not duplicates."""
    response1 = client_with_imports.post("/api/imports/apple-health")
    days1 = response1.json()["days_imported"]

    response2 = client_with_imports.post("/api/imports/apple-health")
    days2 = response2.json()["days_imported"]

    assert days1 == days2  # Same count, not doubled

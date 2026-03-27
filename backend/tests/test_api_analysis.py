import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.db.models import DailyEntry, PainRecord, AppleHealthRecord
from backend.api.dependencies import get_db
from backend.api.main import app


@pytest.fixture()
def client_with_data(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    session = TestSession()
    import numpy as np
    np.random.seed(42)
    for i in range(30):
        date = datetime.date(2026, 3, 1) + datetime.timedelta(days=i)
        sleep = round(max(3, min(10, np.random.normal(7, 1.5))), 1)
        pain = int(max(0, min(10, 10 - sleep + np.random.normal(0, 1))))
        entry = DailyEntry(date=date)
        entry.pain_records.append(PainRecord(location="lumbar", intensity=pain))
        entry.apple_health_records.append(AppleHealthRecord(sleep_hours=sleep, steps=int(np.random.normal(6000, 2000))))
        session.add(entry)
    session.commit()
    session.close()

    def override_get_db():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_correlation_endpoint(client_with_data):
    response = client_with_data.get("/api/analysis/correlation?var_a=pain_max&var_b=sleep_hours")
    assert response.status_code == 200
    data = response.json()
    assert "coefficient" in data
    assert data["coefficient"] < 0


def test_lag_correlation_endpoint(client_with_data):
    response = client_with_data.get("/api/analysis/lag-correlation?target=pain_max&variable=sleep_hours&max_lag=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_rankings_endpoint(client_with_data):
    response = client_with_data.get("/api/analysis/rankings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "variable" in data[0]


def test_report_endpoint(client_with_data):
    response = client_with_data.get("/api/analysis/report?start_date=2026-03-01&end_date=2026-03-30")
    assert response.status_code == 200
    data = response.json()
    assert "pain" in data
    assert "period" in data
    assert data["period"]["days"] == 30

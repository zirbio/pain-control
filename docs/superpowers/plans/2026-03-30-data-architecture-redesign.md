# Data Architecture Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the data model to eliminate redundant child tables (Mood, Stress, Activity, Nutrition), promote subjective fields to DailyEntry, add supplement tracking, derive stress from HRV, and enable per-location pain correlation analysis.

**Architecture:** Four 1:1 child tables (MoodRecord, StressRecord, ActivityRecord, NutritionRecord) are absorbed into DailyEntry as direct columns. A new block of boolean habit/supplement fields replaces scattered tracking. The analysis engine gains per-location pain columns and a computed stress proxy from HRV. Two true 1:N tables (PainRecord, MedicationRecord) and all auto-imported tables remain unchanged.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, SciPy, Next.js 16, TypeScript, TanStack Query

**Spec:** `docs/superpowers/specs/2026-03-30-data-architecture-redesign-design.md`

---

## File Map

### Files to modify
- `backend/backend/db/models.py` — add new DailyEntry columns, remove 4 model classes + relationships
- `backend/backend/api/schemas.py` — add new DailyEntryCreate/Response fields, remove 8 schemas
- `backend/backend/api/routers/entries.py` — update `_populate_entry`, remove old imports/selectinloads
- `backend/backend/analysis/correlations.py` — per-location pain, stress proxy, read new DailyEntry fields
- `backend/backend/analysis/reports.py` — update activity section to use workout data
- `backend/tests/test_models.py` — update for new model structure
- `backend/tests/test_schemas.py` — update for new schema structure
- `backend/tests/test_api_entries.py` — update payloads and assertions
- `backend/tests/test_correlations.py` — update for new dataframe columns
- `backend/tests/test_reports.py` — update for new model structure
- `dashboard/src/lib/api.ts` — update DailyEntry interface
- `dashboard/src/components/daily-detail.tsx` — read new fields instead of child records
- `dashboard/src/components/coverage-heatmap.tsx` — update category checks
- `dashboard/src/app/page.tsx` — update active days metric
- `.claude/skills/pain-checkin/SKILL.md` — update field mapping and mandatory categories

### Files to create
- `backend/backend/db/migrations/versions/<hash>_expand_daily_entry_fields.py` — Alembic migration: add columns
- `backend/scripts/migrate_child_to_entry.py` — one-time data migration script
- `backend/backend/db/migrations/versions/<hash>_drop_eliminated_tables.py` — Alembic migration: drop tables

---

## Task 1: Alembic Migration — Add New Columns to daily_entries

**Files:**
- Create: `backend/backend/db/migrations/versions/` (auto-generated migration)
- Modify: `backend/backend/db/models.py:19-64`

- [ ] **Step 1: Add new columns to DailyEntry model**

In `backend/backend/db/models.py`, add these columns to the `DailyEntry` class after the `stretching` field (line 30):

```python
    # Mood (promoted from MoodRecord)
    mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood_emotions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stress (optional subjective annotation — level derived from HRV)
    stress_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Activity impact (promoted from ActivityRecord)
    activity_pain_effect: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Daily habits
    alcohol: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    heavy_dinner: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Supplements
    omega3: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    vitamin_d: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    magnesium: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    turmeric: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
```

Note: All nullable=True initially. After data migration, we'll handle NOT NULL via application-level validation (Pydantic schema requires them, DB allows null for historical entries without these fields).

- [ ] **Step 2: Generate Alembic migration**

```bash
cd backend && alembic revision --autogenerate -m "expand daily entry with mood, habits, supplements"
```

- [ ] **Step 3: Review and apply migration**

Review the auto-generated file, then:

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 4: Verify migration applied**

```bash
cd backend && python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///../data/pain-control.db')
cols = [c['name'] for c in inspect(engine).get_columns('daily_entries')]
expected = ['mood_score', 'mood_emotions', 'stress_source', 'activity_pain_effect', 'alcohol', 'heavy_dinner', 'omega3', 'vitamin_d', 'magnesium', 'turmeric']
for e in expected:
    assert e in cols, f'Missing column: {e}'
print('All new columns present')
"
```

- [ ] **Step 5: Commit**

```bash
git add backend/backend/db/models.py backend/backend/db/migrations/versions/
git commit -m "feat(db): add mood, habits, supplements columns to daily_entries"
```

---

## Task 2: Data Migration Script

**Files:**
- Create: `backend/scripts/migrate_child_to_entry.py`

- [ ] **Step 1: Write data migration script**

Create `backend/scripts/migrate_child_to_entry.py`:

```python
"""One-time migration: copy data from child tables into DailyEntry columns.

Run from backend/ directory:
    python scripts/migrate_child_to_entry.py

Idempotent — safe to re-run. Only updates NULL fields on DailyEntry.
"""

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pain-control.db"


def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.begin() as conn:
        # Mood → mood_score, mood_emotions
        conn.execute(text("""
            UPDATE daily_entries SET
                mood_score = (
                    SELECT score FROM mood_records
                    WHERE mood_records.entry_id = daily_entries.id
                    LIMIT 1
                ),
                mood_emotions = (
                    SELECT emotions FROM mood_records
                    WHERE mood_records.entry_id = daily_entries.id
                    LIMIT 1
                )
            WHERE mood_score IS NULL
              AND EXISTS (SELECT 1 FROM mood_records WHERE mood_records.entry_id = daily_entries.id)
        """))

        # Stress → stress_source
        conn.execute(text("""
            UPDATE daily_entries SET
                stress_source = (
                    SELECT source FROM stress_records
                    WHERE stress_records.entry_id = daily_entries.id
                    LIMIT 1
                )
            WHERE stress_source IS NULL
              AND EXISTS (SELECT 1 FROM stress_records WHERE stress_records.entry_id = daily_entries.id)
        """))

        # Activity → activity_pain_effect
        conn.execute(text("""
            UPDATE daily_entries SET
                activity_pain_effect = (
                    SELECT pain_effect FROM activity_records
                    WHERE activity_records.entry_id = daily_entries.id
                      AND pain_effect IS NOT NULL
                    LIMIT 1
                )
            WHERE activity_pain_effect IS NULL
              AND EXISTS (
                  SELECT 1 FROM activity_records
                  WHERE activity_records.entry_id = daily_entries.id
                    AND pain_effect IS NOT NULL
              )
        """))

        # Nutrition → alcohol
        conn.execute(text("""
            UPDATE daily_entries SET
                alcohol = (
                    SELECT alcohol FROM nutrition_records
                    WHERE nutrition_records.entry_id = daily_entries.id
                    LIMIT 1
                )
            WHERE alcohol IS NULL
              AND EXISTS (SELECT 1 FROM nutrition_records WHERE nutrition_records.entry_id = daily_entries.id)
        """))

        # Set defaults for new boolean fields (historical entries)
        conn.execute(text("""
            UPDATE daily_entries SET
                heavy_dinner = 0 WHERE heavy_dinner IS NULL
        """))
        conn.execute(text("""
            UPDATE daily_entries SET
                omega3 = 0 WHERE omega3 IS NULL
        """))
        conn.execute(text("""
            UPDATE daily_entries SET
                vitamin_d = 0 WHERE vitamin_d IS NULL
        """))
        conn.execute(text("""
            UPDATE daily_entries SET
                magnesium = 0 WHERE magnesium IS NULL
        """))
        conn.execute(text("""
            UPDATE daily_entries SET
                turmeric = 0 WHERE turmeric IS NULL
        """))

        # Verify migration
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN mood_score IS NOT NULL THEN 1 ELSE 0 END) as with_mood,
                SUM(CASE WHEN alcohol IS NOT NULL THEN 1 ELSE 0 END) as with_alcohol
            FROM daily_entries
        """)).fetchone()

        mood_in_old = conn.execute(text(
            "SELECT COUNT(DISTINCT entry_id) FROM mood_records"
        )).scalar()

        alcohol_in_old = conn.execute(text(
            "SELECT COUNT(DISTINCT entry_id) FROM nutrition_records WHERE alcohol IS NOT NULL"
        )).scalar()

        print(f"Total entries: {result[0]}")
        print(f"Entries with mood_score: {result[1]} (source records: {mood_in_old})")
        print(f"Entries with alcohol: {result[2]} (source records: {alcohol_in_old})")
        print("Migration complete.")


if __name__ == "__main__":
    migrate()
```

- [ ] **Step 2: Run data migration**

```bash
cd backend && python scripts/migrate_child_to_entry.py
```

Verify output shows matching counts between source records and migrated fields.

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/migrate_child_to_entry.py
git commit -m "chore(db): migrate child table data to daily_entries columns"
```

---

## Task 3: Update Pydantic Schemas

**Files:**
- Modify: `backend/backend/api/schemas.py`
- Modify: `backend/tests/test_schemas.py`

- [ ] **Step 1: Write failing tests for new schema**

Replace `backend/tests/test_schemas.py` entirely:

```python
import datetime

import pytest
from pydantic import ValidationError

from backend.api.schemas import (
    DailyEntryCreate,
    ExtraCreate,
    MedicationRecordCreate,
    PainRecordCreate,
)


def test_pain_record_valid():
    record = PainRecordCreate(
        location="lumbar", intensity=6, pattern="constante", time_of_day="mañana"
    )
    assert record.location == "lumbar"
    assert record.intensity == 6


def test_pain_record_intensity_out_of_range():
    with pytest.raises(ValidationError):
        PainRecordCreate(location="lumbar", intensity=11)
    with pytest.raises(ValidationError):
        PainRecordCreate(location="lumbar", intensity=-1)


def test_daily_entry_create_minimal():
    entry = DailyEntryCreate(
        date=datetime.date(2026, 3, 27),
        stretching=False,
        alcohol=False,
        heavy_dinner=False,
        omega3=False,
        vitamin_d=False,
        magnesium=False,
        turmeric=False,
        mood_score=5,
        pain_records=[PainRecordCreate(location="lumbar", intensity=5)],
    )
    assert entry.date == datetime.date(2026, 3, 27)
    assert entry.stretching is False
    assert entry.mood_score == 5
    assert len(entry.pain_records) == 1


def test_daily_entry_create_missing_mood_score():
    with pytest.raises(ValidationError):
        DailyEntryCreate(
            date=datetime.date(2026, 3, 27),
            stretching=True,
            alcohol=False,
            heavy_dinner=False,
            omega3=False,
            vitamin_d=False,
            magnesium=False,
            turmeric=False,
        )


def test_daily_entry_create_missing_habits():
    with pytest.raises(ValidationError):
        DailyEntryCreate(
            date=datetime.date(2026, 3, 27),
            stretching=True,
            mood_score=5,
            # missing alcohol, heavy_dinner, supplements
        )


def test_daily_entry_create_full():
    entry = DailyEntryCreate(
        date=datetime.date(2026, 3, 27),
        stretching=True,
        alcohol=True,
        heavy_dinner=False,
        omega3=True,
        vitamin_d=True,
        magnesium=True,
        turmeric=False,
        mood_score=6,
        mood_emotions=["cansancio", "tranquilidad"],
        stress_source="laboral",
        activity_pain_effect="mejoró",
        pain_records=[PainRecordCreate(location="lumbar", intensity=5)],
        medication_records=[
            MedicationRecordCreate(
                name="Ibuprofen", dose="75mg", time_taken="08:00", effectiveness=7
            )
        ],
        extras=[ExtraCreate(key="rigidez_matutina", value="7", value_type="integer")],
    )
    assert entry.stretching is True
    assert entry.mood_score == 6
    assert entry.alcohol is True
    assert entry.omega3 is True
    assert len(entry.medication_records) == 1


def test_mood_score_out_of_range():
    with pytest.raises(ValidationError):
        DailyEntryCreate(
            date=datetime.date(2026, 3, 27),
            stretching=True,
            alcohol=False,
            heavy_dinner=False,
            omega3=False,
            vitamin_d=False,
            magnesium=False,
            turmeric=False,
            mood_score=0,
        )
    with pytest.raises(ValidationError):
        DailyEntryCreate(
            date=datetime.date(2026, 3, 27),
            stretching=True,
            alcohol=False,
            heavy_dinner=False,
            omega3=False,
            vitamin_d=False,
            magnesium=False,
            turmeric=False,
            mood_score=11,
        )


def test_extra_create():
    extra = ExtraCreate(key="rigidez_matutina", value="7", value_type="integer")
    assert extra.key == "rigidez_matutina"
    assert extra.value_type == "integer"


def test_pain_record_boundary_values():
    record_min = PainRecordCreate(location="lumbar", intensity=0)
    assert record_min.intensity == 0
    record_max = PainRecordCreate(location="lumbar", intensity=10)
    assert record_max.intensity == 10


def test_mood_score_boundary_values():
    entry_min = DailyEntryCreate(
        date=datetime.date(2026, 3, 27),
        stretching=True,
        alcohol=False,
        heavy_dinner=False,
        omega3=False,
        vitamin_d=False,
        magnesium=False,
        turmeric=False,
        mood_score=1,
    )
    assert entry_min.mood_score == 1
    entry_max = DailyEntryCreate(
        date=datetime.date(2026, 3, 27),
        stretching=True,
        alcohol=False,
        heavy_dinner=False,
        omega3=False,
        vitamin_d=False,
        magnesium=False,
        turmeric=False,
        mood_score=10,
    )
    assert entry_max.mood_score == 10
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_schemas.py -v
```

Expected: FAIL — old schema imports still exist, new fields not yet in DailyEntryCreate.

- [ ] **Step 3: Update schemas.py**

Replace `backend/backend/api/schemas.py` entirely:

```python
import datetime

from pydantic import BaseModel, Field

# --- Create schemas (input) ---


class PainRecordCreate(BaseModel):
    location: str
    intensity: int = Field(ge=0, le=10)
    pattern: str | None = None
    time_of_day: str | None = None
    notes: str | None = None


class MedicationRecordCreate(BaseModel):
    name: str
    dose: str | None = None
    time_taken: str | None = None
    effectiveness: int | None = Field(default=None, ge=0, le=10)


class ExtraCreate(BaseModel):
    key: str
    value: str
    value_type: str = "text"


class DailyEntryCreate(BaseModel):
    date: datetime.date

    # Daily habits (all required)
    stretching: bool
    alcohol: bool
    heavy_dinner: bool

    # Supplements (all required)
    omega3: bool
    vitamin_d: bool
    magnesium: bool
    turmeric: bool

    # Mood (required)
    mood_score: int = Field(ge=1, le=10)
    mood_emotions: list[str] | None = None

    # Optional subjective fields
    stress_source: str | None = None
    activity_pain_effect: str | None = None

    # Child records (1:N)
    pain_records: list[PainRecordCreate] = []
    medication_records: list[MedicationRecordCreate] = []
    extras: list[ExtraCreate] = []


# --- Response schemas (output) ---


class PainRecordResponse(BaseModel):
    id: int
    location: str
    intensity: int
    pattern: str | None
    time_of_day: str | None
    notes: str | None

    model_config = {"from_attributes": True}


class MedicationRecordResponse(BaseModel):
    id: int
    name: str
    dose: str | None
    time_taken: str | None
    effectiveness: int | None

    model_config = {"from_attributes": True}


class WeatherRecordResponse(BaseModel):
    id: int
    temperature_c: float | None
    humidity_pct: float | None
    pressure_hpa: float | None
    pressure_change_hpa: float | None
    conditions: str | None
    location: str | None

    model_config = {"from_attributes": True}


class AppleHealthRecordResponse(BaseModel):
    id: int
    sleep_hours: float | None
    sleep_quality: str | None
    resting_hr: int | None
    hrv_ms: float | None
    steps: int | None
    active_calories: int | None
    spo2_pct: float | None
    sleep_rem_hours: float | None = None
    distance_km: float | None = None
    flights_climbed: int | None = None
    resting_energy_kj: float | None = None
    exercise_intensity: float | None = None
    walking_hr_avg: int | None = None
    vo2_max: float | None = None
    cardio_recovery: float | None = None
    step_length_cm: float | None = None
    walking_asymmetry_pct: float | None = None
    double_support_pct: float | None = None
    walking_speed_kmh: float | None = None
    respiratory_rate: float | None = None
    breathing_disturbances: float | None = None
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    daylight_min: float | None = None

    model_config = {"from_attributes": True}


class ExtraResponse(BaseModel):
    id: int
    key: str
    value: str
    value_type: str
    first_seen: datetime.date | None

    model_config = {"from_attributes": True}


class NutritionImportRecordResponse(BaseModel):
    id: int
    source: str
    calories_kj: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_total_g: float | None = None
    fat_saturated_g: float | None = None
    fiber_g: float | None = None
    sugar_g: float | None = None
    water_ml: float | None = None
    caffeine_mg: float | None = None
    sodium_mg: float | None = None
    potassium_mg: float | None = None
    magnesium_mg: float | None = None
    calcium_mg: float | None = None
    iron_mg: float | None = None
    zinc_mg: float | None = None
    cholesterol_mg: float | None = None
    vitamin_a_mcg: float | None = None
    vitamin_c_mg: float | None = None
    vitamin_d_mcg: float | None = None
    vitamin_e_mg: float | None = None
    vitamin_k_mcg: float | None = None
    vitamin_b6_mg: float | None = None
    vitamin_b12_mcg: float | None = None
    folate_mcg: float | None = None
    niacin_mg: float | None = None

    model_config = {"from_attributes": True}


class WorkoutRecordResponse(BaseModel):
    id: int
    workout_type: str
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    duration_min: float | None = None
    active_energy_kj: float | None = None
    intensity: float | None = None
    max_hr: int | None = None
    avg_hr: int | None = None
    distance_km: float | None = None
    steps: int | None = None

    model_config = {"from_attributes": True}


class DailyEntryResponse(BaseModel):
    id: int
    date: datetime.date
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # Direct fields
    stretching: bool | None = None
    alcohol: bool | None = None
    heavy_dinner: bool | None = None
    omega3: bool | None = None
    vitamin_d: bool | None = None
    magnesium: bool | None = None
    turmeric: bool | None = None
    mood_score: int | None = None
    mood_emotions: str | None = None
    stress_source: str | None = None
    activity_pain_effect: str | None = None

    # Child records (1:N)
    pain_records: list[PainRecordResponse]
    medication_records: list[MedicationRecordResponse]

    # Auto-imported
    weather_records: list[WeatherRecordResponse]
    apple_health_records: list[AppleHealthRecordResponse]
    nutrition_import_records: list[NutritionImportRecordResponse] = []
    workout_records: list[WorkoutRecordResponse] = []
    extras: list[ExtraResponse]

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Run schema tests to verify they pass**

```bash
cd backend && pytest tests/test_schemas.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/backend/api/schemas.py backend/tests/test_schemas.py
git commit -m "refactor(schemas): replace child record schemas with DailyEntry direct fields"
```

---

## Task 4: Update Entries Router

**Files:**
- Modify: `backend/backend/api/routers/entries.py`
- Modify: `backend/tests/test_api_entries.py`

- [ ] **Step 1: Write failing tests for new API contract**

Replace `backend/tests/test_api_entries.py` entirely:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_api_entries.py -v
```

Expected: FAIL — old _populate_entry doesn't handle new fields.

- [ ] **Step 3: Update entries router**

Replace `backend/backend/api/routers/entries.py` entirely:

```python
import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, selectinload

from backend.api.dependencies import get_db
from backend.api.schemas import DailyEntryCreate, DailyEntryResponse
from backend.db.models import (
    DailyEntry,
    Extra,
    MedicationRecord,
    PainRecord,
)

router = APIRouter(prefix="/api/entries", tags=["entries"])


def _populate_entry(entry: DailyEntry, data: DailyEntryCreate) -> None:
    """Populate a DailyEntry with data from the create schema."""
    # Direct fields
    entry.stretching = data.stretching
    entry.alcohol = data.alcohol
    entry.heavy_dinner = data.heavy_dinner
    entry.omega3 = data.omega3
    entry.vitamin_d = data.vitamin_d
    entry.magnesium = data.magnesium
    entry.turmeric = data.turmeric
    entry.mood_score = data.mood_score
    entry.mood_emotions = json.dumps(data.mood_emotions) if data.mood_emotions else None
    entry.stress_source = data.stress_source
    entry.activity_pain_effect = data.activity_pain_effect

    # Child records (1:N)
    entry.pain_records = [PainRecord(**r.model_dump()) for r in data.pain_records]
    entry.medication_records = [MedicationRecord(**r.model_dump()) for r in data.medication_records]
    entry.extras = [
        Extra(key=e.key, value=e.value, value_type=e.value_type, first_seen=data.date)
        for e in data.extras
    ]


@router.post("", response_model=DailyEntryResponse)
def create_or_update_entry(
    data: DailyEntryCreate, response: Response, db: Session = Depends(get_db)
):
    existing = db.query(DailyEntry).filter(DailyEntry.date == data.date).first()
    if existing:
        _populate_entry(existing, data)
        db.commit()
        db.refresh(existing)
        response.status_code = 200
        return existing

    entry = DailyEntry(date=data.date)
    _populate_entry(entry, data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    response.status_code = 201
    return entry


@router.get("/{date}", response_model=DailyEntryResponse)
def get_entry_by_date(date: datetime.date, db: Session = Depends(get_db)):
    entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"No entry for {date}")
    return entry


@router.get("", response_model=list[DailyEntryResponse])
def list_entries(
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    limit: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    query = db.query(DailyEntry).options(
        selectinload(DailyEntry.pain_records),
        selectinload(DailyEntry.medication_records),
        selectinload(DailyEntry.weather_records),
        selectinload(DailyEntry.apple_health_records),
        selectinload(DailyEntry.nutrition_import_records),
        selectinload(DailyEntry.workout_records),
        selectinload(DailyEntry.extras),
    )
    if start_date:
        query = query.filter(DailyEntry.date >= start_date)
    if end_date:
        query = query.filter(DailyEntry.date <= end_date)
    return query.order_by(DailyEntry.date.desc()).limit(limit).all()


@router.delete("/{date}", status_code=204)
def delete_entry(date: datetime.date, db: Session = Depends(get_db)):
    entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"No entry for {date}")
    db.delete(entry)
    db.commit()
```

- [ ] **Step 4: Run API tests**

```bash
cd backend && pytest tests/test_api_entries.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/backend/api/routers/entries.py backend/tests/test_api_entries.py
git commit -m "refactor(api): update entries router for new DailyEntry schema"
```

---

## Task 5: Update Model Tests

**Files:**
- Modify: `backend/tests/test_models.py`

- [ ] **Step 1: Update model tests for new structure**

Replace `backend/tests/test_models.py` entirely:

```python
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.db.models import (
    AppleHealthRecord,
    DailyEntry,
    Extra,
    MedicationRecord,
    PainRecord,
    SchemaField,
    WeatherRecord,
)


def _make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_create_daily_entry_with_pain_records(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 27), mood_score=6, stretching=True)
    entry.pain_records.append(
        PainRecord(location="lumbar", intensity=6, pattern="constante", time_of_day="mañana")
    )
    entry.pain_records.append(PainRecord(location="left_knee", intensity=3, time_of_day="tarde"))
    session.add(entry)
    session.commit()

    result = session.query(DailyEntry).first()
    assert result.date == datetime.date(2026, 3, 27)
    assert result.mood_score == 6
    assert len(result.pain_records) == 2
    assert result.pain_records[0].location == "lumbar"
    assert result.pain_records[0].intensity == 6
    assert result.pain_records[1].location == "left_knee"


def test_create_full_entry_with_all_fields(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(
        date=datetime.date(2026, 3, 27),
        stretching=True,
        alcohol=False,
        heavy_dinner=True,
        omega3=True,
        vitamin_d=True,
        magnesium=True,
        turmeric=False,
        mood_score=6,
        mood_emotions='["cansancio"]',
        stress_source="laboral",
        activity_pain_effect="mejoró",
    )
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.medication_records.append(
        MedicationRecord(name="Ibuprofen", dose="400mg", time_taken="08:00", effectiveness=7)
    )
    entry.weather_records.append(
        WeatherRecord(
            temperature_c=14.5,
            humidity_pct=78,
            pressure_hpa=1008.3,
            pressure_change_hpa=-5.2,
            conditions="lluvia",
            location="London",
        )
    )
    entry.apple_health_records.append(
        AppleHealthRecord(
            sleep_hours=6.5, resting_hr=62, hrv_ms=38.5, steps=8432, active_calories=340
        )
    )
    entry.extras.append(Extra(key="rigidez_matutina", value="7", value_type="integer"))
    session.add(entry)
    session.commit()

    result = session.query(DailyEntry).first()
    assert result.mood_score == 6
    assert result.alcohol is False
    assert result.heavy_dinner is True
    assert result.omega3 is True
    assert result.stress_source == "laboral"
    assert result.activity_pain_effect == "mejoró"
    assert len(result.pain_records) == 1
    assert len(result.medication_records) == 1
    assert len(result.weather_records) == 1
    assert len(result.apple_health_records) == 1
    assert len(result.extras) == 1
    assert result.extras[0].key == "rigidez_matutina"


def test_daily_entry_date_unique(tmp_path):
    import pytest
    import sqlalchemy

    session = _make_session(tmp_path)
    session.add(DailyEntry(date=datetime.date(2026, 3, 27)))
    session.commit()
    session.add(DailyEntry(date=datetime.date(2026, 3, 27)))
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        session.commit()


def test_schema_field_creation(tmp_path):
    session = _make_session(tmp_path)
    field = SchemaField(
        field_name="rigidez_matutina",
        promoted_date=datetime.date(2026, 3, 27),
        table_name="pain_records",
        description="Morning stiffness level 0-10",
    )
    session.add(field)
    session.commit()
    result = session.query(SchemaField).first()
    assert result.field_name == "rigidez_matutina"


def test_cascade_delete_removes_child_records(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 27))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.medication_records.append(MedicationRecord(name="Ibuprofen"))
    session.add(entry)
    session.commit()
    entry_id = entry.id

    session.delete(entry)
    session.commit()

    assert session.query(PainRecord).filter(PainRecord.entry_id == entry_id).count() == 0
    assert (
        session.query(MedicationRecord).filter(MedicationRecord.entry_id == entry_id).count() == 0
    )
```

- [ ] **Step 2: Run model tests**

```bash
cd backend && pytest tests/test_models.py -v
```

Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_models.py
git commit -m "test(models): update model tests for new DailyEntry schema"
```

---

## Task 6: Update Analysis Engine

**Files:**
- Modify: `backend/backend/analysis/correlations.py`
- Modify: `backend/tests/test_correlations.py`

- [ ] **Step 1: Write failing tests for new analysis features**

Replace `backend/tests/test_correlations.py` entirely:

```python
import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.analysis.correlations import (
    build_daily_dataframe,
    compute_lag_correlation,
    compute_pairwise_correlation,
    compute_stress_proxy,
    rank_pain_correlations,
)
from backend.db.database import Base
from backend.db.models import (
    AppleHealthRecord,
    DailyEntry,
    MedicationRecord,
    NutritionImportRecord,
    PainRecord,
    WeatherRecord,
    WorkoutRecord,
)


def _sample_dataframe() -> pd.DataFrame:
    """30 days of synthetic data with known correlations."""
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range("2026-03-01", periods=30, freq="D")
    sleep = np.random.normal(7, 1.5, 30).clip(3, 10)
    pain = (10 - sleep + np.random.normal(0, 1, 30)).clip(0, 10)
    pressure = np.random.normal(1013, 5, 30)
    steps = np.random.normal(6000, 2000, 30).clip(0, 15000)
    return pd.DataFrame(
        {
            "date": dates,
            "pain_max": pain.round(0).astype(int),
            "sleep_hours": sleep.round(1),
            "pressure_hpa": pressure.round(1),
            "steps": steps.round(0).astype(int),
        }
    ).set_index("date")


def test_pairwise_correlation_returns_coefficient_and_pvalue():
    df = _sample_dataframe()
    result = compute_pairwise_correlation(df, "pain_max", "sleep_hours")
    assert "coefficient" in result
    assert "p_value" in result
    assert "method" in result
    assert -1 <= result["coefficient"] <= 1
    assert result["coefficient"] < 0


def test_lag_correlation():
    df = _sample_dataframe()
    results = compute_lag_correlation(df, "pain_max", "sleep_hours", max_lag=3)
    assert len(results) == 7
    assert all("lag" in r and "coefficient" in r for r in results)
    lag_0 = next(r for r in results if r["lag"] == 0)
    pairwise = compute_pairwise_correlation(df, "pain_max", "sleep_hours")
    assert abs(lag_0["coefficient"] - pairwise["coefficient"]) < 0.01


def test_rank_pain_correlations():
    df = _sample_dataframe()
    rankings = rank_pain_correlations(df, "pain_max")
    assert len(rankings) > 0
    assert all("variable" in r and "coefficient" in r for r in rankings)
    abs_coeffs = [abs(r["coefficient"]) for r in rankings]
    assert abs_coeffs == sorted(abs_coeffs, reverse=True)


# --- build_daily_dataframe tests ---


def _make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_build_daily_dataframe_all_fields(tmp_path):
    """Entry with all fields populated should produce all expected columns."""
    session = _make_session(tmp_path)
    entry = DailyEntry(
        date=datetime.date(2026, 3, 15),
        stretching=True,
        alcohol=True,
        heavy_dinner=False,
        omega3=True,
        vitamin_d=True,
        magnesium=True,
        turmeric=False,
        mood_score=5,
        mood_emotions='["cansancio"]',
        stress_source="laboral",
        activity_pain_effect="mejoró",
    )
    entry.pain_records.append(PainRecord(location="lumbar", intensity=6))
    entry.pain_records.append(PainRecord(location="left_knee", intensity=4))
    entry.medication_records.append(
        MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=7)
    )
    entry.weather_records.append(
        WeatherRecord(
            temperature_c=14.5,
            humidity_pct=78,
            pressure_hpa=1008.3,
            pressure_change_hpa=-5.2,
        )
    )
    entry.apple_health_records.append(
        AppleHealthRecord(
            sleep_hours=6.5,
            resting_hr=62,
            hrv_ms=38.5,
            steps=8432,
            walking_asymmetry_pct=12.5,
            vo2_max=42.0,
            distance_km=5.3,
        )
    )
    entry.nutrition_import_records.append(
        NutritionImportRecord(
            source="apple_health",
            protein_g=120.5,
            carbs_g=200.0,
            caffeine_mg=400.0,
            vitamin_d_mcg=2.5,
        )
    )
    entry.workout_records.append(
        WorkoutRecord(
            workout_type="Pilates",
            duration_min=58.0,
            active_energy_kj=1200.0,
            intensity=5.2,
            max_hr=141,
            avg_hr=110,
        )
    )
    entry.workout_records.append(
        WorkoutRecord(
            workout_type="Ciclismo",
            duration_min=40.0,
            active_energy_kj=950.0,
            intensity=6.9,
            max_hr=172,
            avg_hr=135,
        )
    )
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert len(df) == 1
    # Pain columns (global)
    assert df["pain_max"].iloc[0] == 6
    assert df["pain_mean"].iloc[0] == 5.0
    # Per-location pain
    assert df["pain_lumbar"].iloc[0] == 6
    assert df["pain_left_knee"].iloc[0] == 4
    # DailyEntry direct fields
    assert df["mood_score"].iloc[0] == 5
    assert df["stretching"].iloc[0] == 1
    assert df["alcohol"].iloc[0] == 1
    assert df["heavy_dinner"].iloc[0] == 0
    assert df["omega3"].iloc[0] == 1
    assert df["vitamin_d"].iloc[0] == 1
    assert df["magnesium"].iloc[0] == 1
    assert df["turmeric"].iloc[0] == 0
    # Medication
    assert df["medication_effectiveness"].iloc[0] == 7.0
    # Weather
    assert df["temperature_c"].iloc[0] == 14.5
    assert df["humidity_pct"].iloc[0] == 78
    # Apple Health
    assert df["sleep_hours"].iloc[0] == 6.5
    assert df["resting_hr"].iloc[0] == 62
    assert df["hrv_ms"].iloc[0] == 38.5
    # Nutrition Import
    assert df["protein_g"].iloc[0] == 120.5
    assert df["caffeine_mg"].iloc[0] == 400.0
    # Workout aggregation
    assert df["workout_count"].iloc[0] == 2
    assert df["workout_total_min"].iloc[0] == 98.0
    assert df["workout_max_hr"].iloc[0] == 172


def test_build_daily_dataframe_per_location_pain(tmp_path):
    """Multiple pain locations should produce per-location columns."""
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15), mood_score=5)
    entry.pain_records.append(PainRecord(location="lumbar", intensity=7))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.pain_records.append(PainRecord(location="tobillo_izq", intensity=3))
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert df["pain_lumbar"].iloc[0] == 7  # max of 7 and 5
    assert df["pain_tobillo_izq"].iloc[0] == 3
    assert df["pain_max"].iloc[0] == 7
    assert df["pain_mean"].iloc[0] == 5.0  # (7+5+3)/3


def test_build_daily_dataframe_empty_pain_records(tmp_path):
    """Entry with no pain records should have pain columns as None."""
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15), mood_score=5)
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert len(df) == 1
    assert pd.isna(df["pain_max"].iloc[0])
    assert pd.isna(df["pain_mean"].iloc[0])


def test_build_daily_dataframe_multiple_medications_averaged(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15), mood_score=5)
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.medication_records.append(
        MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=8)
    )
    entry.medication_records.append(
        MedicationRecord(name="Paracetamol", dose="500mg", effectiveness=4)
    )
    entry.medication_records.append(
        MedicationRecord(name="Tramadol", dose="50mg", effectiveness=None)
    )
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert df["medication_effectiveness"].iloc[0] == 6.0


def test_stress_proxy_from_hrv():
    """stress_proxy should be computed from HRV: lower HRV = higher stress."""
    dates = pd.date_range("2026-03-01", periods=30, freq="D")
    # Baseline HRV ~50ms, day 15 has low HRV (high stress)
    import numpy as np

    np.random.seed(42)
    hrv = np.random.normal(50, 5, 30)
    hrv[14] = 20  # Notably low HRV day

    df = pd.DataFrame({"hrv_ms": hrv}, index=dates)
    result = compute_stress_proxy(df["hrv_ms"])

    assert len(result) == 30
    # Day 15 (low HRV) should have higher stress proxy than average
    assert result.iloc[14] > result.median()
    # All values should be 0-10
    assert result.min() >= 0
    assert result.max() <= 10


def test_pairwise_correlation_constant_column():
    dates = pd.date_range("2026-03-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "pain_max": [3, 5, 7, 4, 6, 8, 2, 5, 7, 3],
            "constant_col": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        },
        index=dates,
    )

    result = compute_pairwise_correlation(df, "pain_max", "constant_col")

    assert result["coefficient"] is None
    assert result["significant"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest tests/test_correlations.py -v
```

Expected: FAIL — `compute_stress_proxy` doesn't exist, per-location pain columns don't exist.

- [ ] **Step 3: Update correlations.py**

Replace `backend/backend/analysis/correlations.py` entirely:

```python
import datetime
import math

import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session, selectinload

from backend.db.models import (
    DailyEntry,
)

_APPLE_HEALTH_FIELDS = [
    "sleep_hours",
    "resting_hr",
    "hrv_ms",
    "steps",
    "active_calories",
    "spo2_pct",
    "sleep_rem_hours",
    "distance_km",
    "flights_climbed",
    "resting_energy_kj",
    "exercise_intensity",
    "walking_hr_avg",
    "vo2_max",
    "cardio_recovery",
    "step_length_cm",
    "walking_asymmetry_pct",
    "double_support_pct",
    "walking_speed_kmh",
    "respiratory_rate",
    "breathing_disturbances",
    "weight_kg",
    "body_fat_pct",
    "daylight_min",
]

_NUTRITION_IMPORT_FIELDS = [
    "calories_kj",
    "protein_g",
    "carbs_g",
    "fat_total_g",
    "fat_saturated_g",
    "fiber_g",
    "sugar_g",
    "water_ml",
    "caffeine_mg",
    "sodium_mg",
    "potassium_mg",
    "magnesium_mg",
    "calcium_mg",
    "iron_mg",
    "zinc_mg",
    "cholesterol_mg",
    "vitamin_d_mcg",
    "vitamin_c_mg",
    "vitamin_a_mcg",
    "vitamin_e_mg",
    "vitamin_k_mcg",
    "vitamin_b6_mg",
    "vitamin_b12_mcg",
    "folate_mcg",
    "niacin_mg",
]

_DAILY_ENTRY_BOOL_FIELDS = [
    "stretching",
    "alcohol",
    "heavy_dinner",
    "omega3",
    "vitamin_d",
    "magnesium",
    "turmeric",
]


def compute_stress_proxy(hrv_series: pd.Series, window: int = 30) -> pd.Series:
    """Derive stress proxy (0-10) from HRV: lower HRV relative to baseline = higher stress.

    Uses a rolling window to compute personal baseline. Returns inverted, normalized score.
    """
    baseline = hrv_series.rolling(window=window, min_periods=5, center=True).median()
    # Fill edges with expanding median
    baseline = baseline.fillna(hrv_series.expanding(min_periods=1).median())

    # Deviation: how far below baseline (positive = more stressed)
    deviation = (baseline - hrv_series) / baseline.clip(lower=1)

    # Normalize to 0-10 scale using sigmoid-like mapping
    # deviation of 0 → stress ~5 (neutral), positive deviation → higher stress
    stress = 5 + 5 * deviation.clip(lower=-1, upper=1)
    return stress.clip(lower=0, upper=10).round(1)


def build_daily_dataframe(
    db: Session,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> pd.DataFrame:
    """Build a flat daily DataFrame from all record types for analysis."""
    query = db.query(DailyEntry).options(
        selectinload(DailyEntry.pain_records),
        selectinload(DailyEntry.medication_records),
        selectinload(DailyEntry.weather_records),
        selectinload(DailyEntry.apple_health_records),
        selectinload(DailyEntry.nutrition_import_records),
        selectinload(DailyEntry.workout_records),
    )
    if start_date:
        query = query.filter(DailyEntry.date >= start_date)
    if end_date:
        query = query.filter(DailyEntry.date <= end_date)
    entries = query.order_by(DailyEntry.date).all()

    # Collect all pain locations across all entries for per-location columns
    all_locations: set[str] = set()
    for entry in entries:
        for p in entry.pain_records:
            all_locations.add(p.location)

    rows = []
    for entry in entries:
        row: dict = {"date": entry.date}

        # Boolean fields from DailyEntry → int
        for field in _DAILY_ENTRY_BOOL_FIELDS:
            val = getattr(entry, field, None)
            row[field] = int(val) if val is not None else None

        # Mood from DailyEntry
        row["mood_score"] = entry.mood_score

        # Pain: global aggregates
        if entry.pain_records:
            intensities = [p.intensity for p in entry.pain_records]
            row["pain_max"] = max(intensities)
            row["pain_mean"] = round(sum(intensities) / len(intensities), 1)

            # Per-location pain (max intensity per location)
            loc_max: dict[str, int] = {}
            for p in entry.pain_records:
                loc_max[p.location] = max(loc_max.get(p.location, 0), p.intensity)
            for loc in all_locations:
                row[f"pain_{loc}"] = loc_max.get(loc)
        else:
            row["pain_max"] = None
            row["pain_mean"] = None
            for loc in all_locations:
                row[f"pain_{loc}"] = None

        # Medication effectiveness average
        effs = [m.effectiveness for m in entry.medication_records if m.effectiveness is not None]
        row["medication_effectiveness"] = round(sum(effs) / len(effs), 1) if effs else None

        # Weather (first record)
        w = entry.weather_records[0] if entry.weather_records else None
        for field in ("temperature_c", "humidity_pct", "pressure_hpa", "pressure_change_hpa"):
            row[field] = getattr(w, field, None)

        # Apple Health (first record)
        ah = entry.apple_health_records[0] if entry.apple_health_records else None
        for field in _APPLE_HEALTH_FIELDS:
            row[field] = getattr(ah, field, None) if ah else None

        # Nutrition Import (first record)
        ni = entry.nutrition_import_records[0] if entry.nutrition_import_records else None
        for field in _NUTRITION_IMPORT_FIELDS:
            row[field] = getattr(ni, field, None) if ni else None

        # Workout aggregation
        wrs = entry.workout_records
        row["workout_count"] = len(wrs)
        row["workout_total_min"] = sum(w.duration_min or 0 for w in wrs)
        row["workout_total_energy_kj"] = sum(w.active_energy_kj or 0 for w in wrs)
        hrs = [w.max_hr for w in wrs if w.max_hr]
        row["workout_max_hr"] = max(hrs) if hrs else None
        avgs = [w.avg_hr for w in wrs if w.avg_hr]
        row["workout_avg_hr"] = round(sum(avgs) / len(avgs)) if avgs else None
        workout_intensities = [w.intensity for w in wrs if w.intensity is not None]
        row["workout_max_intensity"] = max(workout_intensities) if workout_intensities else None

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    # Compute stress proxy from HRV if available
    if "hrv_ms" in df.columns and df["hrv_ms"].notna().sum() >= 5:
        df["stress_proxy"] = compute_stress_proxy(df["hrv_ms"])

    return df


def _null_pairwise(n: int, method: str) -> dict:
    return {"coefficient": None, "p_value": None, "n": n, "method": method, "significant": False}


def compute_pairwise_correlation(
    df: pd.DataFrame, var_a: str, var_b: str, method: str = "spearman"
) -> dict:
    clean = df[[var_a, var_b]].dropna()
    if len(clean) < 5:
        return _null_pairwise(len(clean), method)

    if method == "spearman":
        coeff, p_value = stats.spearmanr(clean[var_a], clean[var_b])
    else:
        coeff, p_value = stats.pearsonr(clean[var_a], clean[var_b])

    coeff_f = float(coeff)
    p_value_f = float(p_value)
    if math.isnan(coeff_f) or math.isnan(p_value_f):
        return _null_pairwise(len(clean), method)

    return {
        "coefficient": round(coeff_f, 3),
        "p_value": round(p_value_f, 4),
        "n": len(clean),
        "method": method,
        "significant": bool(p_value_f < 0.05),
    }


def _null_result(lag: int, n: int) -> dict:
    return {"lag": lag, "coefficient": None, "p_value": None, "n": n, "significant": False}


def compute_lag_correlation(
    df: pd.DataFrame, target: str, variable: str, max_lag: int = 3
) -> list[dict]:
    """Compute cross-correlation between target and variable at different time offsets."""
    results = []
    for lag in range(-max_lag, max_lag + 1):
        shifted = df[variable].shift(-lag)

        temp_df = pd.DataFrame({target: df[target], variable: shifted}).dropna()
        if len(temp_df) < 5:
            results.append(_null_result(lag, len(temp_df)))
            continue

        coeff, p_value = stats.spearmanr(temp_df[target], temp_df[variable])
        if math.isnan(coeff):
            results.append(_null_result(lag, len(temp_df)))
            continue

        results.append(
            {
                "lag": lag,
                "coefficient": round(float(coeff), 3),
                "p_value": round(float(p_value), 4),
                "n": len(temp_df),
                "significant": bool(p_value < 0.05),
            }
        )
    return results


def rank_pain_correlations(df: pd.DataFrame, pain_column: str = "pain_max") -> list[dict]:
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if pain_column in numeric_cols:
        numeric_cols.remove(pain_column)

    rankings = []
    for col in numeric_cols:
        result = compute_pairwise_correlation(df, pain_column, col)
        if result["coefficient"] is not None:
            rankings.append({"variable": col, **result})

    rankings.sort(key=lambda r: abs(r["coefficient"]), reverse=True)
    return rankings
```

- [ ] **Step 4: Run correlation tests**

```bash
cd backend && pytest tests/test_correlations.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/backend/analysis/correlations.py backend/tests/test_correlations.py
git commit -m "feat(analysis): per-location pain correlations and HRV stress proxy"
```

---

## Task 7: Update Reports Module + Tests

**Files:**
- Modify: `backend/backend/analysis/reports.py`
- Modify: `backend/tests/test_reports.py`

- [ ] **Step 1: Update reports.py**

The reports module uses `activity_flag` and `activity_minutes` which no longer exist. Replace the activity section with workout-based data. In `backend/backend/analysis/reports.py`, replace the activity section (lines 43-50):

```python
    if "workout_count" in df.columns:
        report["activity"] = {
            "active_days": int((df["workout_count"] > 0).sum()),
            "total_days": len(df),
            "mean_minutes": round(float(df["workout_total_min"].mean()), 0)
            if "workout_total_min" in df.columns
            else None,
        }
```

- [ ] **Step 2: Update test_reports.py**

Replace `backend/tests/test_reports.py` entirely:

```python
import datetime

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.analysis.reports import generate_report
from backend.db.database import Base
from backend.db.models import (
    AppleHealthRecord,
    DailyEntry,
    MedicationRecord,
    PainRecord,
    WorkoutRecord,
)


def _make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _populate_full_data(session, n_days=14):
    """Populate database with full data: pain, sleep, medication, workouts."""
    np.random.seed(42)
    base_date = datetime.date(2026, 3, 1)
    for i in range(n_days):
        entry = DailyEntry(
            date=base_date + datetime.timedelta(days=i),
            mood_score=np.random.randint(3, 8),
            stretching=True,
            alcohol=False,
            heavy_dinner=False,
            omega3=True,
            vitamin_d=True,
            magnesium=True,
            turmeric=False,
        )
        # Pain: two records per day
        entry.pain_records.append(PainRecord(location="lumbar", intensity=np.random.randint(2, 9)))
        entry.pain_records.append(
            PainRecord(location="left_knee", intensity=np.random.randint(1, 6))
        )
        # Medication with effectiveness
        entry.medication_records.append(
            MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=np.random.randint(3, 9))
        )
        # Workout (replaces ActivityRecord)
        entry.workout_records.append(
            WorkoutRecord(
                workout_type="caminata",
                duration_min=float(np.random.randint(15, 60)),
            )
        )
        # Apple Health (sleep)
        entry.apple_health_records.append(
            AppleHealthRecord(
                sleep_hours=round(np.random.uniform(5.0, 9.0), 1),
                resting_hr=np.random.randint(55, 75),
                steps=np.random.randint(3000, 12000),
            )
        )
        session.add(entry)
    session.commit()


def test_report_with_full_data(tmp_path):
    session = _make_session(tmp_path)
    _populate_full_data(session, n_days=14)

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 14),
    )

    assert report["period"]["start"] == "2026-03-01"
    assert report["period"]["end"] == "2026-03-14"
    assert report["period"]["days"] == 14

    assert "pain" in report
    assert 0 <= report["pain"]["mean"] <= 10

    assert "sleep" in report
    assert report["sleep"]["min"] <= report["sleep"]["mean"] <= report["sleep"]["max"]

    assert "activity" in report
    assert report["activity"]["active_days"] == 14
    assert report["activity"]["total_days"] == 14
    assert report["activity"]["mean_minutes"] is not None

    assert "medication" in report
    assert 0 <= report["medication"]["mean_effectiveness"] <= 10

    assert "top_correlations" in report
    assert len(report["top_correlations"]) <= 5


def test_report_with_only_pain_data(tmp_path):
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    for i in range(7):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i), mood_score=5)
        entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 7),
    )

    assert "pain" in report
    assert report["pain"]["mean"] == 5.0
    assert "sleep" not in report
    assert "medication" not in report
    assert "activity" in report
    assert report["activity"]["active_days"] == 0


def test_report_all_pain_max_none(tmp_path):
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    for i in range(5):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i), mood_score=5)
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 5),
    )

    assert "pain" not in report
    assert "period" in report
    assert report["period"]["days"] == 5


def test_report_medication_below_trend_threshold(tmp_path):
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    for i in range(5):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i), mood_score=5)
        entry.pain_records.append(PainRecord(location="lumbar", intensity=4))
        if i < 2:
            entry.medication_records.append(
                MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=7)
            )
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 5),
    )

    assert "medication" in report
    assert report["medication"]["mean_effectiveness"] == 7.0
    assert report["medication"]["trend"] is None


def test_report_empty_dataframe(tmp_path):
    session = _make_session(tmp_path)

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 7),
    )

    assert "error" in report
    assert report["error"] == "No data for this period"


def test_report_good_and_bad_days_thresholds(tmp_path):
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    intensities = [1, 3, 4, 6, 7, 9, 10, 2, 5, 8]
    for i, intensity in enumerate(intensities):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i), mood_score=5)
        entry.pain_records.append(PainRecord(location="lumbar", intensity=intensity))
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 10),
    )

    assert report["pain"]["good_days"] == 3
    assert report["pain"]["bad_days"] == 4
```

- [ ] **Step 3: Run report tests**

```bash
cd backend && pytest tests/test_reports.py -v
```

Expected: ALL PASS

- [ ] **Step 4: Run full backend test suite**

```bash
cd backend && pytest --cov=backend --cov-report=term-missing
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/backend/analysis/reports.py backend/tests/test_reports.py
git commit -m "refactor(reports): use workout data for activity metrics"
```

---

## Task 8: Remove Old Model Classes + Drop Tables Migration

**Files:**
- Modify: `backend/backend/db/models.py` — remove MoodRecord, StressRecord, ActivityRecord, NutritionRecord classes + relationships
- Create: Alembic migration to drop old tables

- [ ] **Step 1: Remove old model classes from models.py**

In `backend/backend/db/models.py`:

1. Remove the `mood_records` relationship from DailyEntry (line 38-40)
2. Remove the `activity_records` relationship (line 41-43)
3. Remove the `stress_records` relationship (line 44-46)
4. Remove the `nutrition_records` relationship (line 47-49)
5. Remove the entire `MoodRecord` class (lines 98-109)
6. Remove the entire `ActivityRecord` class (lines 112-124)
7. Remove the entire `StressRecord` class (lines 127-138)
8. Remove the entire `NutritionRecord` class (lines 141-154)

The DailyEntry relationships section should only have:
```python
    pain_records: Mapped[list["PainRecord"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    medication_records: Mapped[list["MedicationRecord"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    weather_records: Mapped[list["WeatherRecord"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    apple_health_records: Mapped[list["AppleHealthRecord"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    nutrition_import_records: Mapped[list["NutritionImportRecord"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    workout_records: Mapped[list["WorkoutRecord"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    extras: Mapped[list["Extra"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
```

- [ ] **Step 2: Generate drop-tables migration**

```bash
cd backend && alembic revision --autogenerate -m "drop mood, stress, activity, nutrition tables"
```

Review the generated migration — it should drop 4 tables.

- [ ] **Step 3: Apply migration**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 4: Run full test suite to verify nothing broke**

```bash
cd backend && pytest --cov=backend --cov-report=term-missing
```

Expected: ALL PASS

- [ ] **Step 5: Run linter and formatter**

```bash
cd backend && ruff check . && ruff format --check .
```

- [ ] **Step 6: Commit**

```bash
git add backend/backend/db/models.py backend/backend/db/migrations/versions/
git commit -m "refactor(db): remove eliminated model classes and drop tables"
```

---

## Task 9: Update Frontend

**Files:**
- Modify: `dashboard/src/lib/api.ts`
- Modify: `dashboard/src/components/daily-detail.tsx`
- Modify: `dashboard/src/components/coverage-heatmap.tsx`
- Modify: `dashboard/src/app/page.tsx`

**Important:** Read `dashboard/node_modules/next/dist/docs/` before writing any Next.js code. Next.js 16 has breaking changes.

- [ ] **Step 1: Update TypeScript types in api.ts**

In `dashboard/src/lib/api.ts`, replace the `DailyEntry` interface (lines 105-140):

```typescript
export interface DailyEntry {
  id: number;
  date: string;
  created_at: string;
  updated_at: string;

  // Direct fields
  stretching: boolean | null;
  alcohol: boolean | null;
  heavy_dinner: boolean | null;
  omega3: boolean | null;
  vitamin_d: boolean | null;
  magnesium: boolean | null;
  turmeric: boolean | null;
  mood_score: number | null;
  mood_emotions: string | null;
  stress_source: string | null;
  activity_pain_effect: string | null;

  // Child records (1:N)
  pain_records: PainRecord[];
  medication_records: Array<{
    id: number;
    name: string;
    dose: string | null;
    time_taken: string | null;
    effectiveness: number | null;
  }>;

  // Auto-imported
  weather_records: WeatherRecord[];
  apple_health_records: AppleHealthRecord[];
  nutrition_import_records: NutritionImportRecord[];
  workout_records: WorkoutRecord[];
  extras: Array<{ id: number; key: string; value: string; value_type: string; first_seen: string | null }>;
}
```

- [ ] **Step 2: Update daily-detail.tsx**

Replace the Mood, Activity, Stress, and Nutrition sections. The key changes:

1. Remove `const nutrition = entry.nutrition_records[0] ?? null;` (line 118)
2. Replace mood section (lines 200-227) to read `entry.mood_score` directly
3. Replace activity section (lines 229-258) to show `entry.activity_pain_effect` + workout summary
4. Replace stress section (lines 260-281) to show `entry.stress_source`
5. Replace nutrition section (lines 283-324) to show habits + supplements

Mood section becomes:
```tsx
      {/* Mood */}
      <div>
        <SectionTitle>&Aacute;nimo</SectionTitle>
        {entry.mood_score !== null ? (
          <div className="flex items-center gap-3">
            <span className="font-display text-body tabular-nums text-text-primary">
              {entry.mood_score}/10
            </span>
            {entry.mood_emotions && (
              <span className="font-body text-small text-text-secondary">
                {(() => {
                  try {
                    const parsed = JSON.parse(entry.mood_emotions);
                    return Array.isArray(parsed) ? parsed.join(", ") : entry.mood_emotions;
                  } catch {
                    return entry.mood_emotions;
                  }
                })()}
              </span>
            )}
          </div>
        ) : (
          <EmptyState message="Sin registro de &aacute;nimo" />
        )}
      </div>
```

Replace the Activity section with a Workouts + pain effect section:
```tsx
      {/* Activity & Pain Effect */}
      <div>
        <SectionTitle>Actividad</SectionTitle>
        {entry.workout_records.length > 0 ? (
          <div className="space-y-1.5">
            {entry.workout_records.map((w) => (
              <div key={w.id} className="flex items-center justify-between">
                <span className="font-body text-small text-text-primary capitalize">
                  {w.workout_type}
                </span>
                {w.duration_min !== null && (
                  <span className="font-body text-small text-text-secondary">
                    {Math.round(w.duration_min)} min
                  </span>
                )}
              </div>
            ))}
            {entry.activity_pain_effect && (
              <div className="mt-1">
                <PainEffectLabel effect={entry.activity_pain_effect} />
              </div>
            )}
          </div>
        ) : (
          <EmptyState message="Sin actividad registrada" />
        )}
      </div>
```

Replace Stress section:
```tsx
      {/* Stress */}
      <div>
        <SectionTitle>Estr&eacute;s</SectionTitle>
        {entry.stress_source ? (
          <span className="font-body text-small text-text-secondary">
            {entry.stress_source}
          </span>
        ) : (
          <EmptyState message="Sin fuente de estr&eacute;s anotada" />
        )}
      </div>
```

Replace Nutrition section with Habits + Supplements:
```tsx
      {/* Habits & Supplements */}
      <div>
        <SectionTitle>H&aacute;bitos</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Stretching", value: entry.stretching },
            { label: "Alcohol", value: entry.alcohol },
            { label: "Cena copiosa", value: entry.heavy_dinner },
            { label: "Omega 3", value: entry.omega3 },
            { label: "Vitamina D", value: entry.vitamin_d },
            { label: "Magnesio", value: entry.magnesium },
            { label: "C\u00farcuma", value: entry.turmeric },
          ].map(({ label, value }) => (
            <div key={label}>
              <span className="font-body text-small text-text-muted block">
                {label}
              </span>
              <span className="font-display text-body tabular-nums text-text-primary">
                {value === null ? "\u2014" : value ? "S\u00ed" : "No"}
              </span>
            </div>
          ))}
        </div>
      </div>
```

- [ ] **Step 3: Update coverage-heatmap.tsx**

Replace `MANUAL_CATEGORIES` (lines 22-29):

```typescript
export const MANUAL_CATEGORIES: CategoryDef[] = [
  { key: "pain", label: "Dolor", check: (e) => e.pain_records.length > 0 },
  { key: "medication", label: "Medicación", check: (e) => e.medication_records.length > 0 },
  { key: "mood", label: "Ánimo", check: (e) => e.mood_score !== null },
  { key: "habits", label: "Hábitos", check: (e) => e.stretching !== null },
  { key: "supplements", label: "Suplementos", check: (e) => e.omega3 !== null },
];
```

Update the `buildTooltip` function — replace cases for mood, activity, stress, alcohol (lines 48-64):

```typescript
    case "mood":
      return entry.mood_score !== null ? `${entry.mood_score}/10` : "";
    case "habits": {
      const parts: string[] = [];
      if (entry.stretching) parts.push("Stretching");
      if (entry.alcohol) parts.push("Alcohol");
      if (entry.heavy_dinner) parts.push("Cena copiosa");
      return parts.length > 0 ? parts.join(", ") : "Sin hábitos marcados";
    }
    case "supplements": {
      const supps: string[] = [];
      if (entry.omega3) supps.push("Ω3");
      if (entry.vitamin_d) supps.push("Vit D");
      if (entry.magnesium) supps.push("Mg");
      if (entry.turmeric) supps.push("Cúrcuma");
      return supps.length > 0 ? supps.join(", ") : "Ninguno";
    }
```

- [ ] **Step 4: Update page.tsx active days metric**

In `dashboard/src/app/page.tsx`, replace line 43:

```typescript
  const activeDays = entries?.filter((e) => e.workout_records.length > 0).length ?? 0;
```

- [ ] **Step 5: Run TypeScript check**

```bash
cd dashboard && npx tsc --noEmit
```

Expected: 0 errors

- [ ] **Step 6: Run lint**

```bash
cd dashboard && npm run lint
```

Expected: 0 errors

- [ ] **Step 7: Run build**

```bash
cd dashboard && npm run build
```

Expected: Build succeeds

- [ ] **Step 8: Commit**

```bash
git add dashboard/src/lib/api.ts dashboard/src/components/daily-detail.tsx dashboard/src/components/coverage-heatmap.tsx dashboard/src/app/page.tsx
git commit -m "refactor(dashboard): update frontend for new DailyEntry schema"
```

---

## Task 10: Update Check-in Skill

**Files:**
- Modify: `.claude/skills/pain-checkin/SKILL.md`

- [ ] **Step 1: Update mandatory categories**

Replace the `## Mandatory categories` section (lines 59-89) with:

```markdown
## Mandatory categories

Always ask about ALL sub-fields below. If the user already mentioned some, ask only about the missing ones.

### 1. Dolor
- **ubicación**: dónde duele (lumbar, tobillo, ciática, etc.)
- **intensidad**: 0-10
- **patrón**: constante, intermitente, punzante, sordo, quemante...
- **momento del día**: mañana, tarde, noche, todo el día, al despertar...

### 2. Medicación
- **nombre**: qué tomó (Captor, ibuprofeno, etc.)
- **dosis**: cantidad (75mg, 400mg, etc.)
- **hora toma**: cuándo (HH:MM o aproximado)
- **efectividad**: 0-10, cómo de bien funcionó

### 3. Ánimo
- **puntuación**: 1-10
- **emociones**: las principales del día (frustración, tranquilidad, ansiedad, etc.)

### 4. Hábitos y suplementos
- **stretching**: ¿hiciste estiramientos?
- **alcohol**: ¿bebiste alcohol?
- **cena copiosa**: ¿cenaste demasiado?
- **omega3**: ¿tomaste omega 3?
- **vitamina D**: ¿tomaste vitamina D?
- **magnesio**: ¿tomaste magnesio?
- **cúrcuma**: ¿tomaste cúrcuma?

### 5. Actividad (opcional)
- **efecto en dolor**: ¿la actividad mejoró, empeoró o no cambió el dolor?
  (Solo si es relevante — los workouts se importan de Apple Health)

### Opcionales (solo si el usuario los menciona)
- **Fuente de estrés**: anotación libre (el nivel de estrés se deriva de HRV)
- **Sueño subjetivo**: calidad percibida
- **Extras**: cualquier campo no estándar → extras: [{key, value, value_type}]
```

- [ ] **Step 2: Update field mapping section**

Replace the `## Field mapping` section (lines 130-139) with:

```markdown
## Field mapping

When the user says... → extract:
- "dolor lumbar 6" → pain_records: [{location: "lumbar", intensity: 6}]
- "tobillo 3 intermitente" → pain_records: [{location: "tobillo_izq", intensity: 3, pattern: "intermitente"}]
- "Captor a las 8" → medication_records: [{name: "Captor", dose: "75mg+650mg", time_taken: "08:00"}]
- "ánimo 6, cansado" → mood_score: 6, mood_emotions: ["cansancio"]
- "hice stretching" → stretching: true
- "un par de cervezas" → alcohol: true
- "cena copiosa" / "cené mucho" → heavy_dinner: true
- "tomé las vitaminas" → omega3: true, vitamin_d: true, magnesium: true, turmeric: true
- "solo el magnesio" → magnesium: true (rest false)
- "la actividad mejoró" → activity_pain_effect: "mejoró"
- "estrés laboral" → stress_source: "laboral"
- Any field not recognized → extras: [{key, value, value_type}]
```

- [ ] **Step 3: Update the question block example**

Replace the example (lines 103-124) with:

```markdown
## Question block format

Example for a user who said "ayer lumbar 5, Captor, ánimo 6":

\```
✅ Datos automáticos (Apple Health — 28 mar):
  Sueño: 7.9h (2.3h REM) | FC reposo: 54 bpm | HRV: 119ms
  Pasos: 6,105 | Distancia: 4.6km | Pisos: 13
  SpO2: 98% | Resp: 12/min | Peso: 28.9kg grasa
  Nutrición: 1,627kJ | Proteína: 91.7g | Cafeína: 894mg
  Workout: Fuerza funcional 45min (FC máx 135)
  Estrés derivado (HRV): 4.2/10

✅ Lo que me has contado:
  Dolor lumbar: 5/10
  Captor (tramadol 75mg + paracetamol)
  Ánimo: 6/10

❓ Pendiente por completar:
  Dolor — ¿Fue constante o intermitente? ¿En qué momento del día peor?
  Medicación — ¿A qué hora tomaste el Captor? ¿Cómo de efectivo fue hoy (0-10)?
  Hábitos — ¿Stretching? ¿Alcohol? ¿Cena copiosa?
  Suplementos — ¿Tomaste omega 3, vit D, magnesio, cúrcuma?
  Actividad — ¿La actividad del día afectó al dolor?
\```
```

- [ ] **Step 4: Update the save entry JSON format**

Replace the save entry step (step 7, line 49-55) to reflect the new JSON structure:

```markdown
7. **Save entry**: POST to the API:
   \```bash
   curl -X POST http://localhost:8420/api/entries \
     -H "Content-Type: application/json" \
     -d '{
       "date": "YYYY-MM-DD",
       "stretching": true,
       "alcohol": false,
       "heavy_dinner": false,
       "omega3": true,
       "vitamin_d": true,
       "magnesium": true,
       "turmeric": false,
       "mood_score": 6,
       "mood_emotions": ["cansancio"],
       "stress_source": "laboral",
       "activity_pain_effect": "mejoró",
       "pain_records": [{"location": "lumbar", "intensity": 5, "pattern": "constante", "time_of_day": "mañana"}],
       "medication_records": [{"name": "Captor", "dose": "75mg+650mg", "time_taken": "08:00", "effectiveness": 7}]
     }'
   \```
```

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/pain-checkin/SKILL.md
git commit -m "docs(skill): update pain-checkin for new schema"
```

---

## Task 11: Final Verification

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend && pytest --cov=backend --cov-report=term-missing
```

Expected: ALL PASS, coverage maintained

- [ ] **Step 2: Run backend linter + formatter**

```bash
cd backend && ruff check . && ruff format --check .
```

Expected: 0 issues

- [ ] **Step 3: Run frontend checks**

```bash
cd dashboard && npx tsc --noEmit && npm run lint && npm run build
```

Expected: 0 errors, build succeeds

- [ ] **Step 4: Verify no debug artifacts**

```bash
cd backend && grep -r "console.log\|debugger\|print(" backend/ --include="*.py" | grep -v "test_" | grep -v "__pycache__"
```

Expected: No results (or only legitimate print in migration script)

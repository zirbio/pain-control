# Pain Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal chronic pain tracking system that collects daily data via Claude skills, imports Apple Health metrics, captures weather automatically, and analyzes correlations to discover pain patterns.

**Architecture:** Python FastAPI backend with SQLite storage, React/Next.js dashboard with "Warm Observatory" design system, Claude Code skills for natural language interaction. Three data sources: manual check-in (voice → structured), Apple Health XML import, automatic weather API.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, Alembic, Pandas, SciPy | Next.js, TypeScript, Recharts, Nivo, Tailwind, shadcn/ui, TanStack Query | SQLite | OpenWeatherMap API

**Design Spec:** `docs/superpowers/specs/2026-03-27-pain-control-design.md`

---

## Phase 1: Backend Foundation

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/backend/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `.gitignore`
- Create: `data/imports/.gitkeep`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
build/

# Database
data/*.db
data/*.db-journal

# Environment
.env
.env.local

# Node
node_modules/
.next/
dashboard/.next/
dashboard/node_modules/

# OS
.DS_Store

# IDE
.vscode/
.idea/

# Imports (keep dir, ignore data)
data/imports/*
!data/imports/.gitkeep
```

- [ ] **Step 2: Create backend/pyproject.toml**

```toml
[project]
name = "pain-control-backend"
version = "0.1.0"
description = "Personal chronic pain tracking system — API backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.30",
    "alembic>=1.13.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "pandas>=2.2.0",
    "scipy>=1.13.0",
    "httpx>=0.27.0",
    "apple-health-parser>=0.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM"]
```

- [ ] **Step 3: Create package init files and data directory**

```bash
mkdir -p backend/backend backend/tests data/imports
touch backend/backend/__init__.py backend/tests/__init__.py data/imports/.gitkeep
```

- [ ] **Step 4: Create backend/tests/conftest.py**

```python
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base


@pytest.fixture()
def db_engine(tmp_path):
    """Create a fresh SQLite database for each test."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def db_session(db_engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()
```

- [ ] **Step 5: Create virtual environment and install dependencies**

Run:
```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

- [ ] **Step 6: Verify installation**

Run: `cd backend && source .venv/bin/activate && python -c "import fastapi; import sqlalchemy; import pandas; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add .gitignore backend/pyproject.toml backend/backend/__init__.py backend/tests/__init__.py backend/tests/conftest.py data/imports/.gitkeep
git commit -m "chore: scaffold backend project with dependencies"
```

---

### Task 2: Configuration

**Files:**
- Create: `backend/backend/core/__init__.py`
- Create: `backend/backend/core/config.py`
- Create: `backend/.env.example`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_config.py`:
```python
from backend.core.config import Settings


def test_default_settings():
    settings = Settings(
        OPENWEATHERMAP_API_KEY="test-key",
    )
    assert settings.DATABASE_URL.startswith("sqlite:///")
    assert settings.WEATHER_LOCATION == "London"
    assert settings.DATA_DIR.endswith("data")
    assert settings.IMPORTS_DIR.endswith("imports")


def test_pain_scale_bounds():
    settings = Settings(OPENWEATHERMAP_API_KEY="test-key")
    assert settings.PAIN_SCALE_MIN == 0
    assert settings.PAIN_SCALE_MAX == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement config**

Create `backend/backend/core/__init__.py`:
```python
```

Create `backend/backend/core/config.py`:
```python
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    PROJECT_ROOT: str = str(Path(__file__).resolve().parents[3])
    DATABASE_URL: str = ""
    DATA_DIR: str = ""
    IMPORTS_DIR: str = ""

    # Weather
    OPENWEATHERMAP_API_KEY: str = ""
    WEATHER_LOCATION: str = "London"
    WEATHER_LAT: float = 51.5074
    WEATHER_LON: float = -0.1278

    # Pain tracking
    PAIN_SCALE_MIN: int = 0
    PAIN_SCALE_MAX: int = 10

    # API
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Schema evolution
    EXTRAS_PROMOTION_THRESHOLD: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def model_post_init(self, __context) -> None:
        if not self.DATA_DIR:
            self.DATA_DIR = str(Path(self.PROJECT_ROOT) / "data")
        if not self.IMPORTS_DIR:
            self.IMPORTS_DIR = str(Path(self.DATA_DIR) / "imports")
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"sqlite:///{Path(self.DATA_DIR) / 'pain-control.db'}"


def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Create .env.example**

Create `backend/.env.example`:
```bash
OPENWEATHERMAP_API_KEY=your-api-key-here
WEATHER_LOCATION=London
WEATHER_LAT=51.5074
WEATHER_LON=-0.1278
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_config.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/backend/core/ backend/tests/test_config.py backend/.env.example
git commit -m "feat(config): add Settings with env-based configuration"
```

---

### Task 3: Database models (SQLAlchemy)

**Files:**
- Create: `backend/backend/db/__init__.py`
- Create: `backend/backend/db/database.py`
- Create: `backend/backend/db/models.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_models.py`:
```python
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.db.models import (
    DailyEntry,
    PainRecord,
    MedicationRecord,
    MoodRecord,
    ActivityRecord,
    StressRecord,
    NutritionRecord,
    WeatherRecord,
    AppleHealthRecord,
    Extra,
    SchemaField,
)


def _make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_create_daily_entry_with_pain_records(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 27))
    entry.pain_records.append(
        PainRecord(location="lumbar", intensity=6, pattern="constante", time_of_day="mañana")
    )
    entry.pain_records.append(
        PainRecord(location="left_knee", intensity=3, time_of_day="tarde")
    )
    session.add(entry)
    session.commit()

    result = session.query(DailyEntry).first()
    assert result.date == datetime.date(2026, 3, 27)
    assert len(result.pain_records) == 2
    assert result.pain_records[0].location == "lumbar"
    assert result.pain_records[0].intensity == 6
    assert result.pain_records[1].location == "left_knee"


def test_create_full_entry_with_all_record_types(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 27))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.medication_records.append(
        MedicationRecord(name="Ibuprofen", dose="400mg", time_taken="08:00", effectiveness=7)
    )
    entry.mood_records.append(MoodRecord(score=6, emotions='["cansancio"]'))
    entry.activity_records.append(
        ActivityRecord(type="caminata", duration_min=30, pain_effect="mejoró")
    )
    entry.stress_records.append(StressRecord(level=7, source="laboral"))
    entry.nutrition_records.append(
        NutritionRecord(meals='[{"meal": "almuerzo", "description": "ensalada"}]', alcohol=False, caffeine_cups=2, water_liters=1.5)
    )
    entry.weather_records.append(
        WeatherRecord(temperature_c=14.5, humidity_pct=78, pressure_hpa=1008.3, pressure_change_hpa=-5.2, conditions="lluvia", location="London")
    )
    entry.apple_health_records.append(
        AppleHealthRecord(sleep_hours=6.5, resting_hr=62, hrv_ms=38.5, steps=8432, active_calories=340)
    )
    entry.extras.append(Extra(key="rigidez_matutina", value="7", value_type="integer"))
    session.add(entry)
    session.commit()

    result = session.query(DailyEntry).first()
    assert len(result.pain_records) == 1
    assert len(result.medication_records) == 1
    assert len(result.mood_records) == 1
    assert len(result.activity_records) == 1
    assert len(result.stress_records) == 1
    assert len(result.nutrition_records) == 1
    assert len(result.weather_records) == 1
    assert len(result.apple_health_records) == 1
    assert len(result.extras) == 1
    assert result.extras[0].key == "rigidez_matutina"


def test_daily_entry_date_unique(tmp_path):
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


import pytest
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement database.py**

Create `backend/backend/db/__init__.py`:
```python
```

Create `backend/backend/db/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.core.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_engine(settings.DATABASE_URL, echo=False)


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine)
```

- [ ] **Step 4: Implement models.py**

Create `backend/backend/db/models.py`:
```python
import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


class DailyEntry(Base):
    __tablename__ = "daily_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    pain_records: Mapped[list["PainRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    medication_records: Mapped[list["MedicationRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    mood_records: Mapped[list["MoodRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    activity_records: Mapped[list["ActivityRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    stress_records: Mapped[list["StressRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    nutrition_records: Mapped[list["NutritionRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    weather_records: Mapped[list["WeatherRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    apple_health_records: Mapped[list["AppleHealthRecord"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    extras: Mapped[list["Extra"]] = relationship(back_populates="entry", cascade="all, delete-orphan")


class PainRecord(Base):
    __tablename__ = "pain_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    location: Mapped[str] = mapped_column(String(50), nullable=False)
    intensity: Mapped[int] = mapped_column(Integer, nullable=False)
    pattern: Mapped[str | None] = mapped_column(String(50))
    time_of_day: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    entry: Mapped["DailyEntry"] = relationship(back_populates="pain_records")


class MedicationRecord(Base):
    __tablename__ = "medication_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(100))
    time_taken: Mapped[str | None] = mapped_column(String(10))
    effectiveness: Mapped[int | None] = mapped_column(Integer)

    entry: Mapped["DailyEntry"] = relationship(back_populates="medication_records")


class MoodRecord(Base):
    __tablename__ = "mood_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    emotions: Mapped[str | None] = mapped_column(Text)  # JSON string
    notes: Mapped[str | None] = mapped_column(Text)

    entry: Mapped["DailyEntry"] = relationship(back_populates="mood_records")


class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_min: Mapped[int | None] = mapped_column(Integer)
    pain_effect: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    entry: Mapped["DailyEntry"] = relationship(back_populates="activity_records")


class StressRecord(Base):
    __tablename__ = "stress_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)

    entry: Mapped["DailyEntry"] = relationship(back_populates="stress_records")


class NutritionRecord(Base):
    __tablename__ = "nutrition_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    meals: Mapped[str | None] = mapped_column(Text)  # JSON string
    alcohol: Mapped[bool | None] = mapped_column(Boolean)
    caffeine_cups: Mapped[int | None] = mapped_column(Integer)
    water_liters: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)

    entry: Mapped["DailyEntry"] = relationship(back_populates="nutrition_records")


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    pressure_hpa: Mapped[float | None] = mapped_column(Float)
    pressure_change_hpa: Mapped[float | None] = mapped_column(Float)
    conditions: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(100))

    entry: Mapped["DailyEntry"] = relationship(back_populates="weather_records")


class AppleHealthRecord(Base):
    __tablename__ = "apple_health_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    sleep_quality: Mapped[str | None] = mapped_column(Text)
    resting_hr: Mapped[int | None] = mapped_column(Integer)
    hrv_ms: Mapped[float | None] = mapped_column(Float)
    steps: Mapped[int | None] = mapped_column(Integer)
    active_calories: Mapped[int | None] = mapped_column(Integer)
    spo2_pct: Mapped[float | None] = mapped_column(Float)
    raw_data: Mapped[str | None] = mapped_column(Text)  # JSON string

    entry: Mapped["DailyEntry"] = relationship(back_populates="apple_health_records")


class Extra(Base):
    __tablename__ = "extras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("daily_entries.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    first_seen: Mapped[datetime.date | None] = mapped_column(Date)

    entry: Mapped["DailyEntry"] = relationship(back_populates="extras")


class SchemaField(Base):
    __tablename__ = "schema_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    promoted_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_models.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/backend/db/ backend/tests/test_models.py
git commit -m "feat(db): add SQLAlchemy models for all record types"
```

---

### Task 4: Alembic migrations setup

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/backend/db/migrations/env.py`
- Create: `backend/backend/db/migrations/script.py.mako`
- Create: `backend/backend/db/migrations/versions/` (auto-generated)

- [ ] **Step 1: Initialize Alembic**

Run:
```bash
cd backend && source .venv/bin/activate && alembic init backend/db/migrations
```

- [ ] **Step 2: Configure alembic.ini**

Edit `backend/alembic.ini` — set `script_location`:
```ini
[alembic]
script_location = backend/db/migrations
sqlalchemy.url = sqlite:///%(here)s/../data/pain-control.db
```

- [ ] **Step 3: Configure migrations/env.py**

Replace `backend/backend/db/migrations/env.py`:
```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.db.database import Base
from backend.db import models  # noqa: F401 — ensures models are registered

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Generate initial migration**

Run:
```bash
cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "initial schema"
```
Expected: Creates a file in `backend/backend/db/migrations/versions/`

- [ ] **Step 5: Apply migration**

Run:
```bash
cd backend && source .venv/bin/activate && mkdir -p ../data && alembic upgrade head
```
Expected: Tables created in `data/pain-control.db`

- [ ] **Step 6: Verify migration**

Run:
```bash
cd backend && source .venv/bin/activate && python -c "
import sqlite3
conn = sqlite3.connect('../data/pain-control.db')
tables = [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
print(sorted(tables))
conn.close()
"
```
Expected: List includes `daily_entries`, `pain_records`, `medication_records`, etc.

- [ ] **Step 7: Commit**

```bash
git add backend/alembic.ini backend/backend/db/migrations/
git commit -m "chore(db): configure Alembic with initial migration"
```

---

### Task 5: Pydantic schemas

**Files:**
- Create: `backend/backend/api/__init__.py`
- Create: `backend/backend/api/schemas.py`
- Test: `backend/tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_schemas.py`:
```python
import datetime
import pytest
from pydantic import ValidationError

from backend.api.schemas import (
    PainRecordCreate,
    MedicationRecordCreate,
    MoodRecordCreate,
    ActivityRecordCreate,
    StressRecordCreate,
    NutritionRecordCreate,
    ExtraCreate,
    DailyEntryCreate,
    DailyEntryResponse,
    PainRecordResponse,
)


def test_pain_record_valid():
    record = PainRecordCreate(location="lumbar", intensity=6, pattern="constante", time_of_day="mañana")
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
        pain_records=[PainRecordCreate(location="lumbar", intensity=5)],
    )
    assert entry.date == datetime.date(2026, 3, 27)
    assert len(entry.pain_records) == 1


def test_daily_entry_create_full():
    entry = DailyEntryCreate(
        date=datetime.date(2026, 3, 27),
        pain_records=[PainRecordCreate(location="lumbar", intensity=5)],
        medication_records=[MedicationRecordCreate(name="Ibuprofen", dose="75mg", time_taken="08:00", effectiveness=7)],
        mood_records=[MoodRecordCreate(score=6, emotions=["cansancio"])],
        activity_records=[ActivityRecordCreate(type="caminata", duration_min=30, pain_effect="mejoró")],
        stress_records=[StressRecordCreate(level=7, source="laboral")],
        nutrition_records=[NutritionRecordCreate(alcohol=True, caffeine_cups=2)],
        extras=[ExtraCreate(key="rigidez_matutina", value="7", value_type="integer")],
    )
    assert len(entry.medication_records) == 1
    assert entry.nutrition_records[0].alcohol is True


def test_mood_score_out_of_range():
    with pytest.raises(ValidationError):
        MoodRecordCreate(score=0)
    with pytest.raises(ValidationError):
        MoodRecordCreate(score=11)


def test_extra_create():
    extra = ExtraCreate(key="rigidez_matutina", value="7", value_type="integer")
    assert extra.key == "rigidez_matutina"
    assert extra.value_type == "integer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement schemas**

Create `backend/backend/api/__init__.py`:
```python
```

Create `backend/backend/api/schemas.py`:
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


class MoodRecordCreate(BaseModel):
    score: int = Field(ge=1, le=10)
    emotions: list[str] | None = None
    notes: str | None = None


class ActivityRecordCreate(BaseModel):
    type: str
    duration_min: int | None = None
    pain_effect: str | None = None
    notes: str | None = None


class StressRecordCreate(BaseModel):
    level: int = Field(ge=1, le=10)
    source: str | None = None
    notes: str | None = None


class NutritionRecordCreate(BaseModel):
    meals: list[dict] | None = None
    alcohol: bool | None = None
    caffeine_cups: int | None = None
    water_liters: float | None = None
    notes: str | None = None


class ExtraCreate(BaseModel):
    key: str
    value: str
    value_type: str = "text"


class DailyEntryCreate(BaseModel):
    date: datetime.date
    pain_records: list[PainRecordCreate] = []
    medication_records: list[MedicationRecordCreate] = []
    mood_records: list[MoodRecordCreate] = []
    activity_records: list[ActivityRecordCreate] = []
    stress_records: list[StressRecordCreate] = []
    nutrition_records: list[NutritionRecordCreate] = []
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


class MoodRecordResponse(BaseModel):
    id: int
    score: int
    emotions: str | None
    notes: str | None

    model_config = {"from_attributes": True}


class ActivityRecordResponse(BaseModel):
    id: int
    type: str
    duration_min: int | None
    pain_effect: str | None
    notes: str | None

    model_config = {"from_attributes": True}


class StressRecordResponse(BaseModel):
    id: int
    level: int
    source: str | None
    notes: str | None

    model_config = {"from_attributes": True}


class NutritionRecordResponse(BaseModel):
    id: int
    meals: str | None
    alcohol: bool | None
    caffeine_cups: int | None
    water_liters: float | None
    notes: str | None

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

    model_config = {"from_attributes": True}


class ExtraResponse(BaseModel):
    id: int
    key: str
    value: str
    value_type: str
    first_seen: datetime.date | None

    model_config = {"from_attributes": True}


class DailyEntryResponse(BaseModel):
    id: int
    date: datetime.date
    created_at: datetime.datetime
    updated_at: datetime.datetime
    pain_records: list[PainRecordResponse]
    medication_records: list[MedicationRecordResponse]
    mood_records: list[MoodRecordResponse]
    activity_records: list[ActivityRecordResponse]
    stress_records: list[StressRecordResponse]
    nutrition_records: list[NutritionRecordResponse]
    weather_records: list[WeatherRecordResponse]
    apple_health_records: list[AppleHealthRecordResponse]
    extras: list[ExtraResponse]

    model_config = {"from_attributes": True}


class DailyEntrySummary(BaseModel):
    id: int
    date: datetime.date
    max_pain_intensity: int | None
    pain_locations: list[str]

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_schemas.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/backend/api/ backend/tests/test_schemas.py
git commit -m "feat(api): add Pydantic schemas for all record types"
```

---

### Task 6: Entries API router (CRUD)

**Files:**
- Create: `backend/backend/api/routers/__init__.py`
- Create: `backend/backend/api/routers/entries.py`
- Create: `backend/backend/api/dependencies.py`
- Test: `backend/tests/test_api_entries.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_api_entries.py`:
```python
import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.api.dependencies import get_db
from backend.api.main import app


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
    response = client.post("/api/entries", json={
        "date": "2026-03-27",
        "pain_records": [{"location": "lumbar", "intensity": 6, "pattern": "constante"}],
        "medication_records": [{"name": "Ibuprofen", "dose": "75mg", "time_taken": "08:00", "effectiveness": 7}],
        "mood_records": [{"score": 6}],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["date"] == "2026-03-27"
    assert len(data["pain_records"]) == 1
    assert data["pain_records"][0]["location"] == "lumbar"
    assert data["pain_records"][0]["intensity"] == 6


def test_create_entry_duplicate_date_updates(client):
    client.post("/api/entries", json={
        "date": "2026-03-27",
        "pain_records": [{"location": "lumbar", "intensity": 6}],
    })
    response = client.post("/api/entries", json={
        "date": "2026-03-27",
        "pain_records": [{"location": "lumbar", "intensity": 4}],
        "mood_records": [{"score": 7}],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["pain_records"][0]["intensity"] == 4
    assert len(data["mood_records"]) == 1


def test_get_entry_by_date(client):
    client.post("/api/entries", json={
        "date": "2026-03-27",
        "pain_records": [{"location": "lumbar", "intensity": 5}],
    })
    response = client.get("/api/entries/2026-03-27")
    assert response.status_code == 200
    assert response.json()["date"] == "2026-03-27"


def test_get_entry_not_found(client):
    response = client.get("/api/entries/2026-01-01")
    assert response.status_code == 404


def test_list_entries(client):
    client.post("/api/entries", json={"date": "2026-03-25", "pain_records": [{"location": "lumbar", "intensity": 3}]})
    client.post("/api/entries", json={"date": "2026-03-26", "pain_records": [{"location": "lumbar", "intensity": 5}]})
    client.post("/api/entries", json={"date": "2026-03-27", "pain_records": [{"location": "lumbar", "intensity": 7}]})
    response = client.get("/api/entries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Most recent first
    assert data[0]["date"] == "2026-03-27"


def test_list_entries_with_date_range(client):
    client.post("/api/entries", json={"date": "2026-03-25", "pain_records": [{"location": "lumbar", "intensity": 3}]})
    client.post("/api/entries", json={"date": "2026-03-26", "pain_records": [{"location": "lumbar", "intensity": 5}]})
    client.post("/api/entries", json={"date": "2026-03-27", "pain_records": [{"location": "lumbar", "intensity": 7}]})
    response = client.get("/api/entries?start_date=2026-03-26&end_date=2026-03-27")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_entry(client):
    client.post("/api/entries", json={"date": "2026-03-27", "pain_records": [{"location": "lumbar", "intensity": 5}]})
    response = client.delete("/api/entries/2026-03-27")
    assert response.status_code == 204
    response = client.get("/api/entries/2026-03-27")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_api_entries.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement dependencies.py**

Create `backend/backend/api/dependencies.py`:
```python
from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.db.database import get_session_factory


def get_db() -> Generator[Session, None, None]:
    SessionFactory = get_session_factory()
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
```

- [ ] **Step 4: Implement entries router**

Create `backend/backend/api/routers/__init__.py`:
```python
```

Create `backend/backend/api/routers/entries.py`:
```python
import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.schemas import DailyEntryCreate, DailyEntryResponse
from backend.db.models import (
    ActivityRecord,
    AppleHealthRecord,
    DailyEntry,
    Extra,
    MedicationRecord,
    MoodRecord,
    NutritionRecord,
    PainRecord,
    StressRecord,
    WeatherRecord,
)

router = APIRouter(prefix="/api/entries", tags=["entries"])


def _populate_entry(entry: DailyEntry, data: DailyEntryCreate) -> None:
    """Populate a DailyEntry with records from the create schema."""
    entry.pain_records = [
        PainRecord(**r.model_dump()) for r in data.pain_records
    ]
    entry.medication_records = [
        MedicationRecord(**r.model_dump()) for r in data.medication_records
    ]
    entry.mood_records = [
        MoodRecord(
            score=r.score,
            emotions=json.dumps(r.emotions) if r.emotions else None,
            notes=r.notes,
        )
        for r in data.mood_records
    ]
    entry.activity_records = [
        ActivityRecord(**r.model_dump()) for r in data.activity_records
    ]
    entry.stress_records = [
        StressRecord(**r.model_dump()) for r in data.stress_records
    ]
    entry.nutrition_records = [
        NutritionRecord(
            meals=json.dumps(r.meals) if r.meals else None,
            alcohol=r.alcohol,
            caffeine_cups=r.caffeine_cups,
            water_liters=r.water_liters,
            notes=r.notes,
        )
        for r in data.nutrition_records
    ]
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
    query = db.query(DailyEntry)
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

- [ ] **Step 5: Implement main.py**

Create `backend/backend/api/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import entries
from backend.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Pain Control API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entries.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_api_entries.py -v`
Expected: PASS (7 passed)

- [ ] **Step 7: Smoke test the running server**

Run:
```bash
cd backend && source .venv/bin/activate && uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 &
sleep 2
curl -s http://127.0.0.1:8000/api/health
kill %1
```
Expected: `{"status":"ok"}`

- [ ] **Step 8: Commit**

```bash
git add backend/backend/api/
git commit -m "feat(api): add entries CRUD router with FastAPI"
```

---

## Phase 2: Importers

### Task 7: Weather importer (OpenWeatherMap)

**Files:**
- Create: `backend/backend/importers/__init__.py`
- Create: `backend/backend/importers/weather.py`
- Test: `backend/tests/test_weather.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_weather.py`:
```python
import datetime
import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.importers.weather import WeatherImporter, WeatherData


def test_parse_openweathermap_response():
    raw_response = {
        "main": {"temp": 14.5, "humidity": 78, "pressure": 1008},
        "weather": [{"main": "Rain", "description": "light rain"}],
        "name": "London",
    }
    importer = WeatherImporter(api_key="test", lat=40.42, lon=-3.70)
    result = importer.parse_response(raw_response)
    assert isinstance(result, WeatherData)
    assert result.temperature_c == 14.5
    assert result.humidity_pct == 78
    assert result.pressure_hpa == 1008.0
    assert result.conditions == "Rain"
    assert result.location == "London"


def test_compute_pressure_change():
    importer = WeatherImporter(api_key="test", lat=40.42, lon=-3.70)
    change = importer.compute_pressure_change(
        current=1008.0,
        yesterday=1013.2,
    )
    assert abs(change - (-5.2)) < 0.01


def test_compute_pressure_change_no_yesterday():
    importer = WeatherImporter(api_key="test", lat=40.42, lon=-3.70)
    change = importer.compute_pressure_change(current=1008.0, yesterday=None)
    assert change is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_weather.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement weather importer**

Create `backend/backend/importers/__init__.py`:
```python
```

Create `backend/backend/importers/weather.py`:
```python
from dataclasses import dataclass

import httpx


@dataclass
class WeatherData:
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    pressure_change_hpa: float | None
    conditions: str
    location: str


class WeatherImporter:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str, lat: float, lon: float):
        self.api_key = api_key
        self.lat = lat
        self.lon = lon

    def parse_response(self, data: dict) -> WeatherData:
        return WeatherData(
            temperature_c=data["main"]["temp"],
            humidity_pct=data["main"]["humidity"],
            pressure_hpa=float(data["main"]["pressure"]),
            pressure_change_hpa=None,  # computed separately
            conditions=data["weather"][0]["main"] if data.get("weather") else "Unknown",
            location=data.get("name", "Unknown"),
        )

    def compute_pressure_change(
        self, current: float, yesterday: float | None
    ) -> float | None:
        if yesterday is None:
            return None
        return round(current - yesterday, 2)

    def fetch_current(self) -> WeatherData:
        """Fetch current weather from OpenWeatherMap API."""
        response = httpx.get(
            self.BASE_URL,
            params={
                "lat": self.lat,
                "lon": self.lon,
                "appid": self.api_key,
                "units": "metric",
            },
            timeout=10,
        )
        response.raise_for_status()
        return self.parse_response(response.json())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_weather.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/backend/importers/ backend/tests/test_weather.py
git commit -m "feat(importers): add OpenWeatherMap weather importer"
```

---

### Task 8: Apple Health XML importer

**Files:**
- Create: `backend/backend/importers/apple_health.py`
- Test: `backend/tests/test_apple_health.py`
- Create: `backend/tests/fixtures/sample_health_export.xml`

- [ ] **Step 1: Create a minimal test fixture XML**

Create `backend/tests/fixtures/sample_health_export.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE HealthData [
<!ATTLIST Record type CDATA "">
<!ATTLIST Record sourceName CDATA "">
<!ATTLIST Record unit CDATA "">
<!ATTLIST Record value CDATA "">
<!ATTLIST Record startDate CDATA "">
<!ATTLIST Record endDate CDATA "">
<!ATTLIST Record creationDate CDATA "">
]>
<HealthData locale="es_ES">
 <Record type="HKQuantityTypeIdentifierStepCount" sourceName="Apple Watch" unit="count" value="8432" startDate="2026-03-27 00:00:00 +0100" endDate="2026-03-27 23:59:59 +0100" creationDate="2026-03-27 23:59:59 +0100"/>
 <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Apple Watch" unit="count/min" value="62" startDate="2026-03-27 08:00:00 +0100" endDate="2026-03-27 08:00:00 +0100" creationDate="2026-03-27 08:05:00 +0100"/>
 <Record type="HKQuantityTypeIdentifierRestingHeartRate" sourceName="Apple Watch" unit="count/min" value="58" startDate="2026-03-27 06:00:00 +0100" endDate="2026-03-27 06:00:00 +0100" creationDate="2026-03-27 06:05:00 +0100"/>
 <Record type="HKQuantityTypeIdentifierHeartRateVariabilitySDNN" sourceName="Apple Watch" unit="ms" value="38.5" startDate="2026-03-27 07:00:00 +0100" endDate="2026-03-27 07:00:00 +0100" creationDate="2026-03-27 07:05:00 +0100"/>
 <Record type="HKQuantityTypeIdentifierActiveEnergyBurned" sourceName="Apple Watch" unit="kcal" value="340" startDate="2026-03-27 00:00:00 +0100" endDate="2026-03-27 23:59:59 +0100" creationDate="2026-03-27 23:59:59 +0100"/>
 <Record type="HKQuantityTypeIdentifierOxygenSaturation" sourceName="Apple Watch" unit="%" value="0.97" startDate="2026-03-27 03:00:00 +0100" endDate="2026-03-27 03:00:00 +0100" creationDate="2026-03-27 03:05:00 +0100"/>
 <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Apple Watch" value="HKCategoryValueSleepAnalysisAsleepCore" startDate="2026-03-26 23:30:00 +0100" endDate="2026-03-27 02:00:00 +0100" creationDate="2026-03-27 07:00:00 +0100"/>
 <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Apple Watch" value="HKCategoryValueSleepAnalysisAsleepDeep" startDate="2026-03-27 02:00:00 +0100" endDate="2026-03-27 04:00:00 +0100" creationDate="2026-03-27 07:00:00 +0100"/>
 <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Apple Watch" value="HKCategoryValueSleepAnalysisAsleepREM" startDate="2026-03-27 04:00:00 +0100" endDate="2026-03-27 06:00:00 +0100" creationDate="2026-03-27 07:00:00 +0100"/>
</HealthData>
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_apple_health.py`:
```python
import datetime
from pathlib import Path

import pytest

from backend.importers.apple_health import AppleHealthImporter, DailyHealthData


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_xml_extracts_daily_data():
    importer = AppleHealthImporter()
    results = importer.parse_xml(FIXTURES_DIR / "sample_health_export.xml")
    assert len(results) >= 1
    day = results[datetime.date(2026, 3, 27)]
    assert isinstance(day, DailyHealthData)
    assert day.steps == 8432
    assert day.resting_hr == 58
    assert abs(day.hrv_ms - 38.5) < 0.1
    assert day.active_calories == 340
    assert day.spo2_pct is not None
    assert abs(day.spo2_pct - 97.0) < 0.1


def test_parse_xml_computes_sleep_hours():
    importer = AppleHealthImporter()
    results = importer.parse_xml(FIXTURES_DIR / "sample_health_export.xml")
    day = results[datetime.date(2026, 3, 27)]
    # Sleep: 23:30→02:00 (2.5h) + 02:00→04:00 (2h) + 04:00→06:00 (2h) = 6.5h
    assert day.sleep_hours is not None
    assert abs(day.sleep_hours - 6.5) < 0.1


def test_parse_xml_empty_file(tmp_path):
    xml_file = tmp_path / "empty.xml"
    xml_file.write_text('<?xml version="1.0"?><HealthData></HealthData>')
    importer = AppleHealthImporter()
    results = importer.parse_xml(xml_file)
    assert len(results) == 0
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_apple_health.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Implement Apple Health importer**

Create `backend/backend/importers/apple_health.py`:
```python
import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DailyHealthData:
    date: datetime.date
    sleep_hours: float | None = None
    sleep_quality: str | None = None
    resting_hr: int | None = None
    hrv_ms: float | None = None
    steps: int | None = None
    active_calories: int | None = None
    spo2_pct: float | None = None


# Map Apple Health record types to our fields
QUANTITY_TYPES = {
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_hr",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "hrv_ms",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_calories",
    "HKQuantityTypeIdentifierOxygenSaturation": "spo2_pct",
}

SLEEP_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"
ASLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepDeep",
    "HKCategoryValueSleepAnalysisAsleepREM",
    "HKCategoryValueSleepAnalysisAsleepUnspecified",
    "HKCategoryValueSleepAnalysisAsleep",
}


def _parse_date(date_str: str) -> datetime.date:
    """Parse Apple Health date format '2026-03-27 08:00:00 +0100' to date."""
    return datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S").date()


def _parse_datetime(date_str: str) -> datetime.datetime:
    """Parse Apple Health date format to datetime."""
    return datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")


class AppleHealthImporter:
    def parse_xml(self, xml_path: Path) -> dict[datetime.date, DailyHealthData]:
        """Parse Apple Health export XML and return daily aggregated data."""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Accumulators per day
        daily_steps: dict[datetime.date, int] = defaultdict(int)
        daily_calories: dict[datetime.date, int] = defaultdict(int)
        daily_resting_hr: dict[datetime.date, list[float]] = defaultdict(list)
        daily_hrv: dict[datetime.date, list[float]] = defaultdict(list)
        daily_spo2: dict[datetime.date, list[float]] = defaultdict(list)
        daily_sleep_minutes: dict[datetime.date, float] = defaultdict(float)
        all_dates: set[datetime.date] = set()

        for record in root.iter("Record"):
            record_type = record.get("type", "")
            start_str = record.get("startDate", "")
            end_str = record.get("endDate", "")
            value_str = record.get("value", "")

            if not start_str:
                continue

            date = _parse_date(start_str)
            all_dates.add(date)

            if record_type == "HKQuantityTypeIdentifierStepCount":
                daily_steps[date] += int(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierActiveEnergyBurned":
                daily_calories[date] += int(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierRestingHeartRate":
                daily_resting_hr[date].append(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierHeartRateVariabilitySDNN":
                daily_hrv[date].append(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierOxygenSaturation":
                pct = float(value_str)
                if pct <= 1.0:
                    pct *= 100  # Convert 0.97 → 97
                daily_spo2[date].append(pct)
            elif record_type == SLEEP_TYPE and value_str in ASLEEP_VALUES:
                if end_str:
                    start_dt = _parse_datetime(start_str)
                    end_dt = _parse_datetime(end_str)
                    minutes = (end_dt - start_dt).total_seconds() / 60
                    # Assign sleep to the end date (the morning you wake up)
                    sleep_date = _parse_date(end_str)
                    daily_sleep_minutes[sleep_date] += minutes
                    all_dates.add(sleep_date)

        # Build results
        results: dict[datetime.date, DailyHealthData] = {}
        for date in sorted(all_dates):
            data = DailyHealthData(date=date)
            if date in daily_steps:
                data.steps = daily_steps[date]
            if date in daily_calories:
                data.active_calories = daily_calories[date]
            if date in daily_resting_hr:
                data.resting_hr = int(sum(daily_resting_hr[date]) / len(daily_resting_hr[date]))
            if date in daily_hrv:
                data.hrv_ms = round(sum(daily_hrv[date]) / len(daily_hrv[date]), 1)
            if date in daily_spo2:
                data.spo2_pct = round(sum(daily_spo2[date]) / len(daily_spo2[date]), 1)
            if date in daily_sleep_minutes:
                data.sleep_hours = round(daily_sleep_minutes[date] / 60, 1)
            results[date] = data

        return results
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_apple_health.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
mkdir -p backend/tests/fixtures
git add backend/backend/importers/apple_health.py backend/tests/test_apple_health.py backend/tests/fixtures/
git commit -m "feat(importers): add Apple Health XML parser with daily aggregation"
```

---

### Task 9: Import API router

**Files:**
- Create: `backend/backend/api/routers/imports.py`
- Modify: `backend/backend/api/main.py`
- Test: `backend/tests/test_api_imports.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_api_imports.py`:
```python
import datetime
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.db.models import DailyEntry
from backend.api.dependencies import get_db
from backend.api.main import app


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def client_with_imports(tmp_path):
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

    # Patch imports dir
    from backend.importers import apple_health as ah_module
    original_parse = ah_module.AppleHealthImporter.parse_xml

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.routers.imports.get_imports_dir", lambda: str(imports_dir))
        yield TestClient(app)

    app.dependency_overrides.clear()


def test_import_apple_health(client_with_imports):
    response = client_with_imports.post("/api/imports/apple-health")
    assert response.status_code == 200
    data = response.json()
    assert data["files_processed"] == 1
    assert data["days_imported"] >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_api_imports.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement imports router**

Create `backend/backend/api/routers/imports.py`:
```python
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.core.config import get_settings
from backend.db.models import AppleHealthRecord, DailyEntry
from backend.importers.apple_health import AppleHealthImporter

router = APIRouter(prefix="/api/imports", tags=["imports"])


def get_imports_dir() -> str:
    return get_settings().IMPORTS_DIR


@router.post("/apple-health")
def import_apple_health(db: Session = Depends(get_db)):
    imports_dir = Path(get_imports_dir())
    if not imports_dir.exists():
        return {"files_processed": 0, "days_imported": 0, "errors": ["imports directory not found"]}

    xml_files = list(imports_dir.glob("*.xml"))
    if not xml_files:
        return {"files_processed": 0, "days_imported": 0, "errors": []}

    importer = AppleHealthImporter()
    total_days = 0
    errors = []

    for xml_file in xml_files:
        try:
            daily_data = importer.parse_xml(xml_file)
            for date, health_data in daily_data.items():
                entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
                if not entry:
                    entry = DailyEntry(date=date)
                    db.add(entry)
                    db.flush()

                # Remove existing apple health records for this day
                db.query(AppleHealthRecord).filter(
                    AppleHealthRecord.entry_id == entry.id
                ).delete()

                record = AppleHealthRecord(
                    entry_id=entry.id,
                    sleep_hours=health_data.sleep_hours,
                    resting_hr=health_data.resting_hr,
                    hrv_ms=health_data.hrv_ms,
                    steps=health_data.steps,
                    active_calories=health_data.active_calories,
                    spo2_pct=health_data.spo2_pct,
                )
                db.add(record)
                total_days += 1

            db.commit()
        except Exception as e:
            errors.append(f"{xml_file.name}: {e}")

    return {
        "files_processed": len(xml_files),
        "days_imported": total_days,
        "errors": errors,
    }
```

- [ ] **Step 4: Register imports router in main.py**

Add to `backend/backend/api/main.py` after the entries import:
```python
from backend.api.routers import entries, imports
```
And add:
```python
app.include_router(imports.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_api_imports.py -v`
Expected: PASS (1 passed)

- [ ] **Step 6: Run all tests**

Run: `cd backend && source .venv/bin/activate && pytest -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/backend/api/routers/imports.py backend/backend/api/main.py backend/tests/test_api_imports.py
git commit -m "feat(api): add Apple Health import endpoint"
```

---

## Phase 3: Analysis Engine

### Task 10: Correlation analysis

**Files:**
- Create: `backend/backend/analysis/__init__.py`
- Create: `backend/backend/analysis/correlations.py`
- Test: `backend/tests/test_correlations.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_correlations.py`:
```python
import datetime

import pandas as pd
import pytest

from backend.analysis.correlations import (
    build_daily_dataframe,
    compute_pairwise_correlation,
    compute_lag_correlation,
    rank_pain_correlations,
)


def _sample_dataframe() -> pd.DataFrame:
    """30 days of synthetic data with known correlations."""
    import numpy as np
    np.random.seed(42)
    dates = pd.date_range("2026-03-01", periods=30, freq="D")
    sleep = np.random.normal(7, 1.5, 30).clip(3, 10)
    # Pain inversely correlated with sleep (r ≈ -0.5)
    pain = (10 - sleep + np.random.normal(0, 1, 30)).clip(0, 10)
    pressure = np.random.normal(1013, 5, 30)
    steps = np.random.normal(6000, 2000, 30).clip(0, 15000)
    return pd.DataFrame({
        "date": dates,
        "pain_max": pain.round(0).astype(int),
        "sleep_hours": sleep.round(1),
        "pressure_hpa": pressure.round(1),
        "steps": steps.round(0).astype(int),
    }).set_index("date")


def test_pairwise_correlation_returns_coefficient_and_pvalue():
    df = _sample_dataframe()
    result = compute_pairwise_correlation(df, "pain_max", "sleep_hours")
    assert "coefficient" in result
    assert "p_value" in result
    assert "method" in result
    assert -1 <= result["coefficient"] <= 1
    # Sleep should be negatively correlated with pain in our synthetic data
    assert result["coefficient"] < 0


def test_lag_correlation():
    df = _sample_dataframe()
    results = compute_lag_correlation(df, "pain_max", "sleep_hours", max_lag=3)
    assert len(results) == 7  # lags -3 to +3
    assert all("lag" in r and "coefficient" in r for r in results)
    # Lag 0 should match pairwise
    lag_0 = next(r for r in results if r["lag"] == 0)
    pairwise = compute_pairwise_correlation(df, "pain_max", "sleep_hours")
    assert abs(lag_0["coefficient"] - pairwise["coefficient"]) < 0.01


def test_rank_pain_correlations():
    df = _sample_dataframe()
    rankings = rank_pain_correlations(df, "pain_max")
    assert len(rankings) > 0
    assert all("variable" in r and "coefficient" in r for r in rankings)
    # Should be sorted by absolute coefficient descending
    abs_coeffs = [abs(r["coefficient"]) for r in rankings]
    assert abs_coeffs == sorted(abs_coeffs, reverse=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_correlations.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement correlations.py**

Create `backend/backend/analysis/__init__.py`:
```python
```

Create `backend/backend/analysis/correlations.py`:
```python
import datetime

import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from backend.db.models import (
    ActivityRecord,
    AppleHealthRecord,
    DailyEntry,
    Extra,
    MedicationRecord,
    MoodRecord,
    NutritionRecord,
    PainRecord,
    StressRecord,
    WeatherRecord,
)


def build_daily_dataframe(db: Session, start_date: datetime.date | None = None, end_date: datetime.date | None = None) -> pd.DataFrame:
    """Build a flat daily DataFrame from all record types for analysis."""
    query = db.query(DailyEntry)
    if start_date:
        query = query.filter(DailyEntry.date >= start_date)
    if end_date:
        query = query.filter(DailyEntry.date <= end_date)
    entries = query.order_by(DailyEntry.date).all()

    rows = []
    for entry in entries:
        row: dict = {"date": entry.date}

        # Pain: max intensity, mean intensity
        if entry.pain_records:
            intensities = [p.intensity for p in entry.pain_records]
            row["pain_max"] = max(intensities)
            row["pain_mean"] = round(sum(intensities) / len(intensities), 1)
        else:
            row["pain_max"] = None
            row["pain_mean"] = None

        # Medication: effectiveness mean
        if entry.medication_records:
            effs = [m.effectiveness for m in entry.medication_records if m.effectiveness is not None]
            row["medication_effectiveness"] = round(sum(effs) / len(effs), 1) if effs else None
        else:
            row["medication_effectiveness"] = None

        # Mood
        if entry.mood_records:
            row["mood_score"] = entry.mood_records[0].score
        else:
            row["mood_score"] = None

        # Activity: total minutes, any activity flag
        if entry.activity_records:
            row["activity_minutes"] = sum(a.duration_min or 0 for a in entry.activity_records)
            row["activity_flag"] = 1
        else:
            row["activity_minutes"] = 0
            row["activity_flag"] = 0

        # Stress
        if entry.stress_records:
            row["stress_level"] = entry.stress_records[0].level
        else:
            row["stress_level"] = None

        # Nutrition
        if entry.nutrition_records:
            n = entry.nutrition_records[0]
            row["alcohol"] = int(n.alcohol) if n.alcohol is not None else None
            row["caffeine_cups"] = n.caffeine_cups
            row["water_liters"] = n.water_liters
        else:
            row["alcohol"] = None
            row["caffeine_cups"] = None
            row["water_liters"] = None

        # Weather
        if entry.weather_records:
            w = entry.weather_records[0]
            row["temperature_c"] = w.temperature_c
            row["humidity_pct"] = w.humidity_pct
            row["pressure_hpa"] = w.pressure_hpa
            row["pressure_change_hpa"] = w.pressure_change_hpa
        else:
            row["temperature_c"] = None
            row["humidity_pct"] = None
            row["pressure_hpa"] = None
            row["pressure_change_hpa"] = None

        # Apple Health
        if entry.apple_health_records:
            ah = entry.apple_health_records[0]
            row["sleep_hours"] = ah.sleep_hours
            row["resting_hr"] = ah.resting_hr
            row["hrv_ms"] = ah.hrv_ms
            row["steps"] = ah.steps
            row["active_calories"] = ah.active_calories
            row["spo2_pct"] = ah.spo2_pct
        else:
            row["sleep_hours"] = None
            row["resting_hr"] = None
            row["hrv_ms"] = None
            row["steps"] = None
            row["active_calories"] = None
            row["spo2_pct"] = None

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df


def compute_pairwise_correlation(
    df: pd.DataFrame, var_a: str, var_b: str, method: str = "spearman"
) -> dict:
    """Compute correlation between two columns with significance test."""
    clean = df[[var_a, var_b]].dropna()
    if len(clean) < 5:
        return {"coefficient": None, "p_value": None, "n": len(clean), "method": method, "significant": False}

    if method == "spearman":
        coeff, p_value = stats.spearmanr(clean[var_a], clean[var_b])
    else:
        coeff, p_value = stats.pearsonr(clean[var_a], clean[var_b])

    return {
        "coefficient": round(coeff, 3),
        "p_value": round(p_value, 4),
        "n": len(clean),
        "method": method,
        "significant": p_value < 0.05,
    }


def compute_lag_correlation(
    df: pd.DataFrame, target: str, variable: str, max_lag: int = 3
) -> list[dict]:
    """Compute cross-correlation with temporal lags."""
    results = []
    for lag in range(-max_lag, max_lag + 1):
        if lag == 0:
            shifted = df[variable]
        else:
            shifted = df[variable].shift(-lag)

        temp_df = pd.DataFrame({target: df[target], variable: shifted}).dropna()
        if len(temp_df) < 5:
            results.append({"lag": lag, "coefficient": None, "p_value": None, "n": len(temp_df)})
            continue

        coeff, p_value = stats.spearmanr(temp_df[target], temp_df[variable])
        results.append({
            "lag": lag,
            "coefficient": round(coeff, 3),
            "p_value": round(p_value, 4),
            "n": len(temp_df),
            "significant": p_value < 0.05,
        })
    return results


def rank_pain_correlations(
    df: pd.DataFrame, pain_column: str = "pain_max"
) -> list[dict]:
    """Rank all variables by their correlation with pain."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if pain_column in numeric_cols:
        numeric_cols.remove(pain_column)

    rankings = []
    for col in numeric_cols:
        result = compute_pairwise_correlation(df, pain_column, col)
        if result["coefficient"] is not None:
            rankings.append({
                "variable": col,
                "coefficient": result["coefficient"],
                "p_value": result["p_value"],
                "n": result["n"],
                "significant": result["significant"],
            })

    rankings.sort(key=lambda r: abs(r["coefficient"]), reverse=True)
    return rankings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_correlations.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/backend/analysis/ backend/tests/test_correlations.py
git commit -m "feat(analysis): add pairwise, lag, and ranked correlation analysis"
```

---

### Task 11: Trends and reports

**Files:**
- Create: `backend/backend/analysis/trends.py`
- Create: `backend/backend/analysis/reports.py`
- Test: `backend/tests/test_trends.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_trends.py`:
```python
import numpy as np
import pandas as pd
import pytest

from backend.analysis.trends import (
    compute_moving_average,
    compute_trend_direction,
    compare_periods,
)


def _sample_df():
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    np.random.seed(42)
    pain = (np.linspace(6, 4, 60) + np.random.normal(0, 0.5, 60)).clip(0, 10).round(1)
    return pd.DataFrame({"pain_max": pain}, index=dates)


def test_moving_average():
    df = _sample_df()
    result = compute_moving_average(df, "pain_max", window=7)
    assert "pain_max_ma7" in result.columns
    assert result["pain_max_ma7"].iloc[6] is not None
    assert pd.isna(result["pain_max_ma7"].iloc[0])


def test_trend_direction_detects_decrease():
    df = _sample_df()
    trend = compute_trend_direction(df, "pain_max")
    assert trend["direction"] == "decreasing"
    assert trend["slope"] < 0


def test_compare_periods():
    df = _sample_df()
    result = compare_periods(
        df, "pain_max",
        period_a_start="2026-01-01", period_a_end="2026-01-30",
        period_b_start="2026-02-01", period_b_end="2026-03-01",
    )
    assert "period_a_mean" in result
    assert "period_b_mean" in result
    assert "difference" in result
    assert "p_value" in result
    # Period B should have lower pain (decreasing trend)
    assert result["period_b_mean"] < result["period_a_mean"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_trends.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement trends.py**

Create `backend/backend/analysis/trends.py`:
```python
import pandas as pd
import numpy as np
from scipy import stats


def compute_moving_average(df: pd.DataFrame, column: str, window: int = 7) -> pd.DataFrame:
    """Add a moving average column to the dataframe."""
    result = df.copy()
    result[f"{column}_ma{window}"] = result[column].rolling(window=window).mean().round(1)
    return result


def compute_trend_direction(df: pd.DataFrame, column: str) -> dict:
    """Compute trend direction using linear regression."""
    clean = df[[column]].dropna()
    if len(clean) < 3:
        return {"direction": "insufficient_data", "slope": 0, "r_squared": 0}

    x = np.arange(len(clean))
    y = clean[column].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    if p_value > 0.05:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    return {
        "direction": direction,
        "slope": round(slope, 4),
        "r_squared": round(r_value ** 2, 3),
        "p_value": round(p_value, 4),
    }


def compare_periods(
    df: pd.DataFrame,
    column: str,
    period_a_start: str,
    period_a_end: str,
    period_b_start: str,
    period_b_end: str,
) -> dict:
    """Compare a metric between two date ranges using Mann-Whitney U test."""
    a = df.loc[period_a_start:period_a_end, column].dropna()
    b = df.loc[period_b_start:period_b_end, column].dropna()

    if len(a) < 3 or len(b) < 3:
        return {
            "period_a_mean": a.mean() if len(a) > 0 else None,
            "period_b_mean": b.mean() if len(b) > 0 else None,
            "difference": None,
            "p_value": None,
            "significant": False,
            "n_a": len(a),
            "n_b": len(b),
        }

    stat, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")

    return {
        "period_a_mean": round(a.mean(), 1),
        "period_b_mean": round(b.mean(), 1),
        "difference": round(b.mean() - a.mean(), 1),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "n_a": len(a),
        "n_b": len(b),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_trends.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Implement reports.py**

Create `backend/backend/analysis/reports.py`:
```python
import datetime

import pandas as pd
from sqlalchemy.orm import Session

from backend.analysis.correlations import build_daily_dataframe, rank_pain_correlations
from backend.analysis.trends import compute_moving_average, compute_trend_direction


def generate_report(
    db: Session,
    start_date: datetime.date,
    end_date: datetime.date,
) -> dict:
    """Generate a structured report for a date range."""
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty:
        return {"error": "No data for this period"}

    report: dict = {
        "period": {"start": str(start_date), "end": str(end_date), "days": len(df)},
    }

    # Pain summary
    if "pain_max" in df.columns:
        pain = df["pain_max"].dropna()
        if len(pain) > 0:
            report["pain"] = {
                "mean": round(pain.mean(), 1),
                "min": int(pain.min()),
                "max": int(pain.max()),
                "good_days": int((pain <= 3).sum()),
                "bad_days": int((pain >= 7).sum()),
                "trend": compute_trend_direction(df, "pain_max"),
            }

    # Sleep summary
    if "sleep_hours" in df.columns:
        sleep = df["sleep_hours"].dropna()
        if len(sleep) > 0:
            report["sleep"] = {
                "mean": round(sleep.mean(), 1),
                "min": round(sleep.min(), 1),
                "max": round(sleep.max(), 1),
            }

    # Activity summary
    if "activity_flag" in df.columns:
        report["activity"] = {
            "active_days": int(df["activity_flag"].sum()),
            "total_days": len(df),
            "mean_minutes": round(df["activity_minutes"].mean(), 0) if "activity_minutes" in df.columns else None,
        }

    # Medication effectiveness
    if "medication_effectiveness" in df.columns:
        eff = df["medication_effectiveness"].dropna()
        if len(eff) > 0:
            report["medication"] = {
                "mean_effectiveness": round(eff.mean(), 1),
                "trend": compute_trend_direction(df, "medication_effectiveness") if len(eff) >= 3 else None,
            }

    # Top correlations
    if "pain_max" in df.columns:
        report["top_correlations"] = rank_pain_correlations(df, "pain_max")[:5]

    return report
```

- [ ] **Step 6: Commit**

```bash
git add backend/backend/analysis/trends.py backend/backend/analysis/reports.py backend/tests/test_trends.py
git commit -m "feat(analysis): add trend analysis, period comparison, and report generation"
```

---

### Task 12: Analysis API router

**Files:**
- Create: `backend/backend/api/routers/analysis.py`
- Modify: `backend/backend/api/main.py`
- Test: `backend/tests/test_api_analysis.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_api_analysis.py`:
```python
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

    # Seed 30 days of data
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
    assert data["coefficient"] < 0  # negative correlation


def test_lag_correlation_endpoint(client_with_data):
    response = client_with_data.get("/api/analysis/lag-correlation?target=pain_max&variable=sleep_hours&max_lag=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # lags -2 to +2


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_api_analysis.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement analysis router**

Create `backend/backend/api/routers/analysis.py`:
```python
import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.analysis.correlations import (
    build_daily_dataframe,
    compute_lag_correlation,
    compute_pairwise_correlation,
    rank_pain_correlations,
)
from backend.analysis.reports import generate_report

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/correlation")
def get_correlation(
    var_a: str = Query(...),
    var_b: str = Query(...),
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty or var_a not in df.columns or var_b not in df.columns:
        return {"error": "Insufficient data or invalid variable names"}
    return compute_pairwise_correlation(df, var_a, var_b)


@router.get("/lag-correlation")
def get_lag_correlation(
    target: str = Query(...),
    variable: str = Query(...),
    max_lag: int = Query(default=3, ge=1, le=7),
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty or target not in df.columns or variable not in df.columns:
        return {"error": "Insufficient data or invalid variable names"}
    return compute_lag_correlation(df, target, variable, max_lag=max_lag)


@router.get("/rankings")
def get_rankings(
    pain_column: str = Query(default="pain_max"),
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty:
        return []
    return rank_pain_correlations(df, pain_column)


@router.get("/report")
def get_report(
    start_date: datetime.date = Query(...),
    end_date: datetime.date = Query(...),
    db: Session = Depends(get_db),
):
    return generate_report(db, start_date, end_date)
```

- [ ] **Step 4: Register analysis router in main.py**

Update `backend/backend/api/main.py` imports:
```python
from backend.api.routers import entries, imports, analysis
```
Add:
```python
app.include_router(analysis.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_api_analysis.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Run full test suite**

Run: `cd backend && source .venv/bin/activate && pytest -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/backend/api/routers/analysis.py backend/backend/api/main.py backend/tests/test_api_analysis.py
git commit -m "feat(api): add analysis endpoints for correlations, lags, rankings, reports"
```

---

## Phase 4: Dashboard Foundation

### Task 13: Next.js project setup + Warm Observatory design system

**Files:**
- Create: `dashboard/` (Next.js scaffold)
- Create: `dashboard/tailwind.config.ts`
- Create: `dashboard/src/styles/globals.css`
- Create: `dashboard/src/lib/design-tokens.ts`
- Create: `dashboard/src/app/layout.tsx`

- [ ] **Step 1: Scaffold Next.js project**

Run:
```bash
npx create-next-app@latest dashboard --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack
```

- [ ] **Step 2: Install dependencies**

Run:
```bash
cd dashboard && npm install recharts @nivo/heatmap @nivo/core @tanstack/react-query date-fns framer-motion && npm install -D @types/node
```

- [ ] **Step 3: Install shadcn/ui**

Run:
```bash
cd dashboard && npx shadcn@latest init -d
```

- [ ] **Step 4: Create design tokens**

Create `dashboard/src/lib/design-tokens.ts`:
```typescript
export const painScale = [
  "#6B8A7A", // 0 — sage
  "#7B9A7E", // 1
  "#8DAA82", // 2
  "#A8B86A", // 3 — sage-lime
  "#C4A84E", // 4
  "#D4A03A", // 5 — amber
  "#D9882A", // 6
  "#D4702A", // 7 — warm orange
  "#C4512A", // 8 — cinnabar
  "#A63A2A", // 9
  "#8B2500", // 10 — deep terracotta
] as const;

export function getPainColor(intensity: number): string {
  const clamped = Math.max(0, Math.min(10, Math.round(intensity)));
  return painScale[clamped];
}

export const atmosphericColors = {
  highPressure: "#2A3040",
  normal: "#1C1917",
  lowPressure: "#2A2018",
} as const;

export const accentColors = {
  positive: "#6B8A7A",
  warning: "#D4A03A",
  negative: "#C4512A",
  info: "#7B9FBF",
  highlight: "#D4A03A",
} as const;
```

- [ ] **Step 5: Configure Tailwind with Warm Observatory palette**

Replace `dashboard/tailwind.config.ts`:
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#1C1917",
          secondary: "#292524",
          tertiary: "#44403C",
          surface: "#1A1412",
        },
        text: {
          primary: "#F5F5F4",
          secondary: "#A8A29E",
          muted: "#78716C",
        },
        pain: {
          0: "#6B8A7A",
          1: "#7B9A7E",
          2: "#8DAA82",
          3: "#A8B86A",
          4: "#C4A84E",
          5: "#D4A03A",
          6: "#D9882A",
          7: "#D4702A",
          8: "#C4512A",
          9: "#A63A2A",
          10: "#8B2500",
        },
        accent: {
          positive: "#6B8A7A",
          warning: "#D4A03A",
          negative: "#C4512A",
          info: "#7B9FBF",
          highlight: "#D4A03A",
        },
      },
      fontFamily: {
        display: ["Newsreader", "Georgia", "serif"],
        body: ["Satoshi", "system-ui", "sans-serif"],
      },
      fontSize: {
        metric: ["3rem", { lineHeight: "1", letterSpacing: "-0.02em" }],
        h1: ["1.75rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        h2: ["1.25rem", { lineHeight: "1.3" }],
        body: ["0.9375rem", { lineHeight: "1.6" }],
        label: ["0.75rem", { lineHeight: "1", letterSpacing: "0.08em" }],
        small: ["0.6875rem", { lineHeight: "1.4" }],
      },
      borderRadius: {
        card: "12px",
      },
    },
  },
  plugins: [],
};
export default config;
```

- [ ] **Step 6: Configure global styles**

Replace `dashboard/src/styles/globals.css` (or `src/app/globals.css` depending on scaffold):
```css
@import "tailwindcss";

@font-face {
  font-family: "Newsreader";
  src: url("https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;0,6..72,600&display=swap");
}

@font-face {
  font-family: "Satoshi";
  src: url("https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap");
}

body {
  background-color: #1c1917;
  color: #f5f5f4;
  font-family: "Satoshi", system-ui, sans-serif;
}

/* Warm shimmer for loading skeletons */
@keyframes warm-shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton {
  background: linear-gradient(90deg, #292524 25%, #44403c 50%, #292524 75%);
  background-size: 200% 100%;
  animation: warm-shimmer 1.5s ease-in-out infinite;
  border-radius: 8px;
}

/* Tabular numbers for data */
.tabular-nums {
  font-variant-numeric: tabular-nums;
}
```

- [ ] **Step 7: Create root layout**

Replace `dashboard/src/app/layout.tsx`:
```tsx
import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Pain Control",
  description: "Personal chronic pain tracking and pattern analysis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500;6..72,600&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-bg-primary text-text-primary font-body antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 8: Create TanStack Query provider**

Create `dashboard/src/app/providers.tsx`:
```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
```

- [ ] **Step 9: Verify build**

Run: `cd dashboard && npm run build`
Expected: Build succeeds

- [ ] **Step 10: Commit**

```bash
git add dashboard/
git commit -m "feat(dashboard): scaffold Next.js with Warm Observatory design system"
```

---

### Task 14: API client hook

**Files:**
- Create: `dashboard/src/lib/api.ts`
- Create: `dashboard/src/hooks/use-entries.ts`
- Create: `dashboard/src/hooks/use-analysis.ts`

- [ ] **Step 1: Create API client**

Create `dashboard/src/lib/api.ts`:
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export interface PainRecord {
  id: number;
  location: string;
  intensity: number;
  pattern: string | null;
  time_of_day: string | null;
  notes: string | null;
}

export interface WeatherRecord {
  id: number;
  temperature_c: number | null;
  humidity_pct: number | null;
  pressure_hpa: number | null;
  pressure_change_hpa: number | null;
  conditions: string | null;
  location: string | null;
}

export interface AppleHealthRecord {
  id: number;
  sleep_hours: number | null;
  resting_hr: number | null;
  hrv_ms: number | null;
  steps: number | null;
  active_calories: number | null;
  spo2_pct: number | null;
}

export interface DailyEntry {
  id: number;
  date: string;
  pain_records: PainRecord[];
  medication_records: Array<{
    id: number;
    name: string;
    dose: string | null;
    time_taken: string | null;
    effectiveness: number | null;
  }>;
  mood_records: Array<{ id: number; score: number; emotions: string | null }>;
  activity_records: Array<{
    id: number;
    type: string;
    duration_min: number | null;
    pain_effect: string | null;
  }>;
  stress_records: Array<{ id: number; level: number; source: string | null }>;
  nutrition_records: Array<{
    id: number;
    alcohol: boolean | null;
    caffeine_cups: number | null;
    water_liters: number | null;
  }>;
  weather_records: WeatherRecord[];
  apple_health_records: AppleHealthRecord[];
  extras: Array<{ id: number; key: string; value: string; value_type: string }>;
}

export interface CorrelationResult {
  coefficient: number | null;
  p_value: number | null;
  n: number;
  method: string;
  significant: boolean;
}

export interface LagCorrelationResult {
  lag: number;
  coefficient: number | null;
  p_value: number | null;
  n: number;
  significant?: boolean;
}

export interface RankingResult {
  variable: string;
  coefficient: number;
  p_value: number;
  n: number;
  significant: boolean;
}

export interface ReportResult {
  period: { start: string; end: string; days: number };
  pain?: {
    mean: number;
    min: number;
    max: number;
    good_days: number;
    bad_days: number;
    trend: { direction: string; slope: number };
  };
  sleep?: { mean: number; min: number; max: number };
  activity?: { active_days: number; total_days: number; mean_minutes: number | null };
  medication?: { mean_effectiveness: number; trend: { direction: string } | null };
  top_correlations?: RankingResult[];
}

export const api = {
  entries: {
    list: (params?: { start_date?: string; end_date?: string; limit?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.set("start_date", params.start_date);
      if (params?.end_date) searchParams.set("end_date", params.end_date);
      if (params?.limit) searchParams.set("limit", String(params.limit));
      const qs = searchParams.toString();
      return fetchApi<DailyEntry[]>(`/api/entries${qs ? `?${qs}` : ""}`);
    },
    get: (date: string) => fetchApi<DailyEntry>(`/api/entries/${date}`),
  },
  analysis: {
    correlation: (varA: string, varB: string) =>
      fetchApi<CorrelationResult>(`/api/analysis/correlation?var_a=${varA}&var_b=${varB}`),
    lagCorrelation: (target: string, variable: string, maxLag = 3) =>
      fetchApi<LagCorrelationResult[]>(
        `/api/analysis/lag-correlation?target=${target}&variable=${variable}&max_lag=${maxLag}`
      ),
    rankings: () => fetchApi<RankingResult[]>("/api/analysis/rankings"),
    report: (startDate: string, endDate: string) =>
      fetchApi<ReportResult>(`/api/analysis/report?start_date=${startDate}&end_date=${endDate}`),
  },
};
```

- [ ] **Step 2: Create entry hooks**

Create `dashboard/src/hooks/use-entries.ts`:
```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useEntries(params?: {
  start_date?: string;
  end_date?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["entries", params],
    queryFn: () => api.entries.list(params),
  });
}

export function useEntry(date: string) {
  return useQuery({
    queryKey: ["entry", date],
    queryFn: () => api.entries.get(date),
    enabled: !!date,
  });
}
```

- [ ] **Step 3: Create analysis hooks**

Create `dashboard/src/hooks/use-analysis.ts`:
```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useCorrelation(varA: string, varB: string) {
  return useQuery({
    queryKey: ["correlation", varA, varB],
    queryFn: () => api.analysis.correlation(varA, varB),
    enabled: !!varA && !!varB,
  });
}

export function useLagCorrelation(target: string, variable: string, maxLag = 3) {
  return useQuery({
    queryKey: ["lag-correlation", target, variable, maxLag],
    queryFn: () => api.analysis.lagCorrelation(target, variable, maxLag),
    enabled: !!target && !!variable,
  });
}

export function useRankings() {
  return useQuery({
    queryKey: ["rankings"],
    queryFn: () => api.analysis.rankings(),
  });
}

export function useReport(startDate: string, endDate: string) {
  return useQuery({
    queryKey: ["report", startDate, endDate],
    queryFn: () => api.analysis.report(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
}
```

- [ ] **Step 4: Verify build**

Run: `cd dashboard && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/lib/api.ts dashboard/src/hooks/
git commit -m "feat(dashboard): add API client and React Query hooks"
```

---

### Task 15: Metric Card + Dashboard page shell

**Files:**
- Create: `dashboard/src/components/metric-card.tsx`
- Create: `dashboard/src/components/nav-bar.tsx`
- Modify: `dashboard/src/app/page.tsx`

- [ ] **Step 1: Create MetricCard component**

Create `dashboard/src/components/metric-card.tsx`:
```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { getPainColor } from "@/lib/design-tokens";

interface MetricCardProps {
  label: string;
  value: number | string | null;
  trend?: { direction: "up" | "down" | "stable"; delta?: string };
  colorScale?: "pain";
  sparklineData?: number[];
  unit?: string;
}

function AnimatedNumber({ value }: { value: number }) {
  const [displayed, setDisplayed] = useState(0);
  const ref = useRef<number>(0);

  useEffect(() => {
    const start = ref.current;
    const end = value;
    const duration = 400;
    const startTime = performance.now();

    function animate(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = start + (end - start) * eased;
      setDisplayed(current);
      ref.current = current;
      if (progress < 1) requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }, [value]);

  return <>{displayed.toFixed(1)}</>;
}

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const h = 24;
  const w = 100;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-6 mt-2" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const trendArrows = { up: "\u2197", down: "\u2198", stable: "\u2192" };

export function MetricCard({
  label,
  value,
  trend,
  colorScale,
  sparklineData,
  unit,
}: MetricCardProps) {
  const numericValue = typeof value === "number" ? value : null;
  const displayColor =
    colorScale === "pain" && numericValue !== null
      ? getPainColor(numericValue)
      : "#F5F5F4";

  return (
    <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(26,20,18,0.5)]">
      <div className="flex items-center justify-between mb-3">
        <span className="font-body text-label uppercase text-text-muted tracking-widest">
          {label}
        </span>
        {trend && (
          <span
            className="text-small"
            style={{
              color:
                trend.direction === "down"
                  ? "#6B8A7A"
                  : trend.direction === "up"
                    ? "#C4512A"
                    : "#78716C",
            }}
          >
            {trendArrows[trend.direction]} {trend.delta}
          </span>
        )}
      </div>
      <div
        className="font-display text-metric tabular-nums"
        style={{ color: displayColor }}
      >
        {numericValue !== null ? (
          <AnimatedNumber value={numericValue} />
        ) : (
          <span className="text-text-muted">{value ?? "—"}</span>
        )}
        {unit && <span className="text-h2 text-text-secondary ml-1">{unit}</span>}
      </div>
      {sparklineData && sparklineData.length > 1 && (
        <MiniSparkline data={sparklineData} color={displayColor} />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create navigation bar**

Create `dashboard/src/components/nav-bar.tsx`:
```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/analysis", label: "Analysis" },
  { href: "/history", label: "History" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-bg-secondary border-t border-bg-tertiary z-50 md:static md:border-t-0 md:border-b">
      <div className="max-w-6xl mx-auto flex items-center justify-center gap-8 px-6 py-3">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`font-body text-body transition-colors ${
                active
                  ? "text-accent-highlight"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
```

- [ ] **Step 3: Create Dashboard page shell**

Replace `dashboard/src/app/page.tsx`:
```tsx
"use client";

import { format, subDays } from "date-fns";
import { es } from "date-fns/locale";
import { MetricCard } from "@/components/metric-card";
import { NavBar } from "@/components/nav-bar";
import { useEntries } from "@/hooks/use-entries";

export default function DashboardPage() {
  const today = new Date();
  const startDate = format(subDays(today, 7), "yyyy-MM-dd");
  const endDate = format(today, "yyyy-MM-dd");
  const { data: entries, isLoading } = useEntries({
    start_date: startDate,
    end_date: endDate,
  });

  const painValues = entries
    ?.map((e) => {
      const max = Math.max(...e.pain_records.map((p) => p.intensity), 0);
      return max;
    })
    .reverse();

  const avgPain =
    painValues && painValues.length > 0
      ? painValues.reduce((a, b) => a + b, 0) / painValues.length
      : null;

  const sleepValues = entries
    ?.map((e) => e.apple_health_records[0]?.sleep_hours ?? null)
    .filter((v): v is number => v !== null)
    .reverse();

  const avgSleep =
    sleepValues && sleepValues.length > 0
      ? sleepValues.reduce((a, b) => a + b, 0) / sleepValues.length
      : null;

  const activeDays =
    entries?.filter((e) => e.activity_records.length > 0).length ?? 0;
  const totalDays = entries?.length ?? 0;

  const medEffValues = entries
    ?.flatMap((e) => e.medication_records)
    .map((m) => m.effectiveness)
    .filter((v): v is number => v !== null);

  const avgMedEff =
    medEffValues && medEffValues.length > 0
      ? medEffValues.reduce((a, b) => a + b, 0) / medEffValues.length
      : null;

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-h1 font-semibold text-text-primary">
            Pain Control
          </h1>
          <p className="font-body text-body text-text-secondary mt-1">
            {format(today, "EEEE, d 'de' MMMM", { locale: es })}
          </p>
        </div>

        {/* Metric Cards */}
        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton h-32" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <MetricCard
              label="Dolor · 7d"
              value={avgPain}
              colorScale="pain"
              sparklineData={painValues}
            />
            <MetricCard
              label="Sueño · 7d"
              value={avgSleep}
              unit="h"
              sparklineData={sleepValues}
            />
            <MetricCard
              label="Activo"
              value={`${activeDays}/${totalDays}`}
              unit="días"
            />
            <MetricCard
              label="Ibuprofen"
              value={avgMedEff}
              unit="/10"
            />
          </div>
        )}

        {/* Placeholder areas for Phase 5 components */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="md:col-span-2 bg-bg-secondary border border-bg-tertiary rounded-card p-6 h-80 flex items-center justify-center">
            <span className="text-text-muted font-body text-body">
              Pain Timeline — Task 16
            </span>
          </div>
          <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-6 h-80 flex items-center justify-center">
            <span className="text-text-muted font-body text-body">
              Weekly Heatmap — Task 17
            </span>
          </div>
        </div>

        <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-6 flex items-center justify-center h-40">
          <span className="text-text-muted font-body text-body">
            Alerts Panel — Task 18
          </span>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Create placeholder pages**

Create `dashboard/src/app/analysis/page.tsx`:
```tsx
import { NavBar } from "@/components/nav-bar";

export default function AnalysisPage() {
  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="font-display text-h1 font-semibold">Analysis</h1>
        <p className="text-text-secondary mt-2 font-body text-body">
          Correlation exploration — Implemented in Phase 5
        </p>
      </main>
    </div>
  );
}
```

Create `dashboard/src/app/history/page.tsx`:
```tsx
import { NavBar } from "@/components/nav-bar";

export default function HistoryPage() {
  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="font-display text-h1 font-semibold">History</h1>
        <p className="text-text-secondary mt-2 font-body text-body">
          Browsable history — Implemented in Phase 5
        </p>
      </main>
    </div>
  );
}
```

- [ ] **Step 5: Verify build**

Run: `cd dashboard && npm run build`
Expected: Build succeeds

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/
git commit -m "feat(dashboard): add MetricCard, NavBar, and Dashboard page shell"
```

---

## Phase 5: Dashboard Components + Analysis & History Pages

### Task 16: Pain Timeline (hero component)

**Files:**
- Create: `dashboard/src/components/pain-timeline.tsx`
- Modify: `dashboard/src/app/page.tsx` (replace placeholder)

This is the signature component. Implementation details:
- Multi-series Recharts LineChart with curveNatural
- Atmospheric background via linearGradient that shifts based on pressure data
- Custom tooltip with full day summary
- Location colors: lower_back=`#C4512A`, left_knee=`#D4A03A`, shoulder=`#A8B86A`

- [ ] **Step 1: Implement PainTimeline**

Create `dashboard/src/components/pain-timeline.tsx` — full Recharts LineChart implementation with:
- Props: `entries: DailyEntry[]`
- Build datasets per pain location from entries
- Atmospheric gradient background derived from weather pressure data
- Custom tooltip showing date, all pain locations, sleep, weather
- curveNatural via `type="natural"` on Recharts `<Line>`
- Axis styling matching design system (stone-500 text, stone-700 gridlines)

- [ ] **Step 2: Integrate into Dashboard page — replace the timeline placeholder**

- [ ] **Step 3: Verify build**

Run: `cd dashboard && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add dashboard/src/components/pain-timeline.tsx dashboard/src/app/page.tsx
git commit -m "feat(dashboard): add PainTimeline with atmospheric background"
```

---

### Task 17: Weekly Heatmap

**Files:**
- Create: `dashboard/src/components/weekly-heatmap.tsx`
- Modify: `dashboard/src/app/page.tsx` (replace placeholder)

- [ ] **Step 1: Implement WeeklyHeatmap**

Create `dashboard/src/components/weekly-heatmap.tsx` — custom SVG/CSS grid component:
- Props: `entries: DailyEntry[]`
- 5 rows (weeks) × 7 columns (days)
- Cell color from `getPainColor(maxIntensity)`
- No-data cells: `bg-bg-secondary` with dashed border
- Hover: scale(1.15) + tooltip with date and pain level
- Cell border-radius: 4px, gap: 3px

- [ ] **Step 2: Integrate into Dashboard page — replace the heatmap placeholder**

- [ ] **Step 3: Verify build and commit**

```bash
git add dashboard/src/components/weekly-heatmap.tsx dashboard/src/app/page.tsx
git commit -m "feat(dashboard): add WeeklyHeatmap component"
```

---

### Task 18: Alert Cards panel

**Files:**
- Create: `dashboard/src/components/alert-card.tsx`
- Create: `dashboard/src/components/alerts-panel.tsx`
- Modify: `dashboard/src/app/page.tsx` (replace placeholder)

- [ ] **Step 1: Implement AlertCard and AlertsPanel**

AlertCard: left border accent (amber 3px, expands to 5px on hover), diamond icon, uppercase label, body text, metadata line (p-value, period).

AlertsPanel: Grid of AlertCards. For now, derive alerts from the report endpoint's top_correlations data.

- [ ] **Step 2: Integrate into Dashboard page**

- [ ] **Step 3: Verify build and commit**

```bash
git add dashboard/src/components/alert-card.tsx dashboard/src/components/alerts-panel.tsx dashboard/src/app/page.tsx
git commit -m "feat(dashboard): add AlertCard and AlertsPanel"
```

---

### Task 19: Analysis page — Correlation Matrix, Lag Explorer, Weather Overlay

**Files:**
- Create: `dashboard/src/components/correlation-matrix.tsx`
- Create: `dashboard/src/components/lag-explorer.tsx`
- Create: `dashboard/src/components/weather-overlay.tsx`
- Create: `dashboard/src/components/period-comparison.tsx`
- Modify: `dashboard/src/app/analysis/page.tsx`

- [ ] **Step 1: Implement CorrelationMatrix**

Nivo HeatMap component (triangular, lower half). Sage for negative, stone-800 for zero, cinnabar for positive. Row/column highlight on hover. Click opens scatter plot detail (can be a later enhancement — for now, show coefficient on click).

- [ ] **Step 2: Implement LagExplorer**

Two dropdowns (target variable, comparison variable) + slider for lag (-3 to +3). Recharts BarChart showing correlation coefficient at each lag. Highlight significant bars.

- [ ] **Step 3: Implement WeatherOverlay**

Dual-axis Recharts ComposedChart: pain line (left Y axis) + pressure area (right Y axis). Same atmospheric background logic as PainTimeline.

- [ ] **Step 4: Implement PeriodComparison**

Two date range pickers. Side-by-side stat cards comparing the periods. Mann-Whitney test result shown.

- [ ] **Step 5: Compose Analysis page**

Wire all four components into `dashboard/src/app/analysis/page.tsx` with section headers and the NavBar.

- [ ] **Step 6: Verify build and commit**

```bash
git add dashboard/src/components/correlation-matrix.tsx dashboard/src/components/lag-explorer.tsx dashboard/src/components/weather-overlay.tsx dashboard/src/components/period-comparison.tsx dashboard/src/app/analysis/page.tsx
git commit -m "feat(dashboard): add Analysis page with correlation matrix, lag explorer, weather overlay"
```

---

### Task 20: History page — Calendar, DailyDetail, Filters

**Files:**
- Create: `dashboard/src/components/calendar-view.tsx`
- Create: `dashboard/src/components/daily-detail.tsx`
- Modify: `dashboard/src/app/history/page.tsx`

- [ ] **Step 1: Implement CalendarView**

Monthly calendar grid. Each day cell shows:
- Date number
- Pain dot (color-coded by max intensity)
- Minimal icons for notable factors

Selected day: amber ring border. Click triggers `onSelectDate(date)`.

Navigation: `<` `>` arrows for month, month/year header in Newsreader.

- [ ] **Step 2: Implement DailyDetail**

Slide-in panel from right (or inline on mobile). Shows all data for a selected day:
- Pain records (each location with intensity bar)
- Medication, mood, activity, stress, nutrition
- Weather conditions
- Apple Health metrics
- Extras

- [ ] **Step 3: Compose History page**

Calendar on the left (2/3), DailyDetail panel on the right (1/3). Filter bar above calendar (pain range, location).

- [ ] **Step 4: Verify build and commit**

```bash
git add dashboard/src/components/calendar-view.tsx dashboard/src/components/daily-detail.tsx dashboard/src/app/history/page.tsx
git commit -m "feat(dashboard): add History page with calendar and daily detail"
```

---

## Phase 6: Claude Skills

### Task 21: pain-checkin skill

**Files:**
- Create: `skills/pain-checkin.md`

- [ ] **Step 1: Write the skill**

Create `skills/pain-checkin.md`:
```markdown
---
name: pain-checkin
description: Daily pain check-in — parse natural language input, extract structured health data, ask for missing fields, save via API
---

# Daily Pain Check-In

Parse the user's free-form description of their day and save structured data.

## Process

1. **Parse input**: Extract all mentioned data points:
   - Pain: location(s), intensity (0-10), pattern, time of day
   - Medication: name, dose, time taken, effectiveness
   - Mood: score (1-10), emotions
   - Activity: type, duration, effect on pain
   - Stress: level (1-10), source
   - Nutrition: meals, alcohol, caffeine, water
   - Extras: any new fields not in the standard schema

2. **Check required fields** — if missing, ask ONE follow-up question:
   - Required: at least one pain record (location + intensity), medication, mood score
   - Frame questions naturally: "¿Tomaste Ibuprofen hoy?" not "Medication name required"

3. **Fetch weather**: Run this command to get today's weather:
   ```bash
   curl -s "http://localhost:8000/api/entries" | head -1  # Check if API is running
   ```
   Then fetch weather via the API (the API auto-fetches from OpenWeatherMap).

4. **Save entry**: POST to the API:
   ```bash
   curl -X POST http://localhost:8000/api/entries \
     -H "Content-Type: application/json" \
     -d '<structured JSON>'
   ```

5. **Report back**: Confirm what was saved. If any alerts from recent data, mention them.

## Field mapping

When the user says... → extract:
- "dolor lumbar 6" → pain_records: [{location: "lumbar", intensity: 6}]
- "tobillo molesta un 3" → pain_records: [{location: "left_knee", intensity: 3}]
- "Ibuprofen a las 8" → medication_records: [{name: "Ibuprofen", dose: "400mg", time_taken: "08:00"}]
- "dormí 5 horas" → this comes from Apple Health import, but note it if mentioned
- "caminé media hora" → activity_records: [{type: "caminata", duration_min: 30}]
- "me ayudó" / "mejoró" → pain_effect: "mejoró"
- "estrés laboral fuerte" → stress_records: [{level: 8, source: "laboral"}]
- "un par de cervezas" → nutrition_records: [{alcohol: true}]
- Any field not recognized → extras: [{key: "field_name", value: "value", value_type: "text|integer|boolean"}]

## Tone

Brief, warm, clinical-but-human. Never minimize pain ("solo un 6"). Acknowledge bad days simply.
```

- [ ] **Step 2: Commit**

```bash
git add skills/pain-checkin.md
git commit -m "feat(skills): add pain-checkin daily check-in skill"
```

---

### Task 22: pain-analyze, pain-report, pain-import, pain-schema skills

**Files:**
- Create: `skills/pain-analyze.md`
- Create: `skills/pain-report.md`
- Create: `skills/pain-import.md`
- Create: `skills/pain-schema.md`

- [ ] **Step 1: Write pain-analyze skill**

Create `skills/pain-analyze.md`:
```markdown
---
name: pain-analyze
description: Answer natural language questions about pain patterns by querying the analysis API — correlations, trends, comparisons
---

# Pain Analysis

Translate the user's question into an API call and present results in natural language.

## Question patterns

| User asks | API call | How to present |
|---|---|---|
| "¿X afecta mi dolor?" | GET /api/analysis/correlation?var_a=pain_max&var_b=X | Coefficient + significance + plain language |
| "¿Qué es lo que más me ayuda/perjudica?" | GET /api/analysis/rankings | Top 5 ranked factors |
| "¿El efecto de X es inmediato o al día siguiente?" | GET /api/analysis/lag-correlation?target=pain_max&variable=X | Show which lag has strongest correlation |
| "Compara febrero vs marzo" | GET /api/analysis/report for each period | Side-by-side stats |
| "¿Cómo voy esta semana?" | GET /api/analysis/report?start_date=...&end_date=... | Weekly summary |
| "¿Cuándo fue mi último brote?" | GET /api/entries?limit=90, then filter pain_max >= 7 | Show date + full context |

## Variable name mapping

Map natural language to column names:
- sueño → sleep_hours
- pasos/caminar → steps
- presión/barométrica → pressure_hpa / pressure_change_hpa
- estrés → stress_level
- ánimo → mood_score
- ejercicio/actividad → activity_minutes / activity_flag
- alcohol → alcohol
- café/cafeína → caffeine_cups
- medicación/Ibuprofen → medication_effectiveness
- frecuencia cardíaca → resting_hr
- HRV/variabilidad → hrv_ms

## Presenting results

- Always include the statistical context (n, p-value, significant or not)
- Use plain language: "significativo" = "hay suficientes datos para confiar en esta correlación"
- For non-significant results: "No hay suficiente evidencia todavía (solo N días de datos)"
- Round to 1 decimal place for readability
```

- [ ] **Step 2: Write pain-report skill**

Create `skills/pain-report.md`:
```markdown
---
name: pain-report
description: Generate structured weekly or monthly pain reports with trends, correlations, and alerts
---

# Pain Report

Generate a formatted report for a given period.

## Usage

`/pain-report semana` — last 7 days
`/pain-report mes` — last 30 days
`/pain-report 2026-01-01 2026-03-31` — custom range

## Process

1. Determine date range from arguments
2. Call: `curl -s "http://localhost:8000/api/analysis/report?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"`
3. Format the response into a readable report

## Report template

```
# Informe [Semanal|Mensual] — [date range]

## Resumen dolor
- Media: X.X/10 ([↑|↓|→] X.X vs periodo anterior)
- Rango: X — X
- Días buenos (≤3): X | Días malos (≥7): X

## Sueño
- Media: X.Xh
- Correlación sueño→dolor: X.XX ([fuerte|moderada|débil])

## Actividad
- X/X días activo
- Días activos: dolor medio X.X vs X.X inactivos

## Medicación
- Efectividad media: X.X/10
- Tendencia: [estable|subiendo|bajando]

## Top correlaciones
1. [variable] → dolor [+|-]X.X (p=X.XX)
2. ...

## Alertas
[Any detected alerts]
```
```

- [ ] **Step 3: Write pain-import skill**

Create `skills/pain-import.md`:
```markdown
---
name: pain-import
description: Import Apple Health data from XML export files in the data/imports directory
---

# Apple Health Import

## Process

1. Check for XML files:
   ```bash
   ls -la data/imports/*.xml 2>/dev/null
   ```

2. If files found, trigger import:
   ```bash
   curl -X POST http://localhost:8000/api/imports/apple-health
   ```

3. Report results: files processed, days imported, any errors.

4. Suggest running `/pain-report` to see updated data.
```

- [ ] **Step 4: Write pain-schema skill**

Create `skills/pain-schema.md`:
```markdown
---
name: pain-schema
description: View and manage the evolving data schema — show active fields, extras in use, promote frequent extras to formal fields
---

# Schema Management

## Show current schema

Query the database for all table structures and extras in use:

```bash
curl -s http://localhost:8000/api/entries?limit=1 | python3 -c "
import json, sys
entry = json.load(sys.stdin)
if isinstance(entry, list) and entry:
    entry = entry[0]
    for key in entry:
        if isinstance(entry[key], list):
            print(f'{key}: {len(entry[key])} records')
        else:
            print(f'{key}: {entry[key]}')
"
```

## Show extras usage

```bash
curl -s "http://localhost:8000/api/entries?limit=365" | python3 -c "
import json, sys
from collections import Counter
entries = json.load(sys.stdin)
extras = Counter()
for e in entries:
    for x in e.get('extras', []):
        extras[x['key']] += 1
for key, count in extras.most_common():
    flag = ' ⚠️ PROMOTE?' if count >= 5 else ''
    print(f'{key}: {count} occurrences{flag}')
"
```

## Promoting a field

When the user approves promotion of an extra field:
1. Generate and run an Alembic migration to add the new column
2. Migrate historical data from extras to the new column
3. Update the pain-checkin skill to include this field
```

- [ ] **Step 5: Commit**

```bash
git add skills/
git commit -m "feat(skills): add pain-analyze, pain-report, pain-import, pain-schema skills"
```

---

## Phase 7: Final Integration

### Task 23: End-to-end smoke test

- [ ] **Step 1: Start backend**

```bash
cd backend && source .venv/bin/activate && uvicorn backend.api.main:app --reload &
```

- [ ] **Step 2: Create a test entry via API**

```bash
curl -X POST http://localhost:8000/api/entries \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-27",
    "pain_records": [{"location": "lumbar", "intensity": 6, "pattern": "constante", "time_of_day": "mañana"}],
    "medication_records": [{"name": "Ibuprofen", "dose": "400mg", "time_taken": "08:00", "effectiveness": 7}],
    "mood_records": [{"score": 5}],
    "activity_records": [{"type": "caminata", "duration_min": 30, "pain_effect": "mejoró"}],
    "stress_records": [{"level": 7, "source": "laboral"}]
  }'
```

- [ ] **Step 3: Verify entry retrieval**

```bash
curl -s http://localhost:8000/api/entries/2026-03-27 | python3 -m json.tool
```

- [ ] **Step 4: Start dashboard**

```bash
cd dashboard && npm run dev &
```

- [ ] **Step 5: Verify dashboard loads at http://localhost:3000**

Open browser, check MetricCards render, NavBar works, pages navigate.

- [ ] **Step 6: Run full backend test suite**

```bash
cd backend && source .venv/bin/activate && pytest -v --tb=short
```
Expected: All tests pass

- [ ] **Step 7: Kill background processes and commit**

```bash
kill %1 %2  # stop uvicorn and next dev
git add -A && git status  # verify nothing unexpected
```

- [ ] **Step 8: Final commit**

```bash
git commit -m "chore: complete Phase 1-7 integration smoke test"
```

---

## Future Phases (not in this plan)

These features are in the spec but deferred beyond the MVP:

- **Pattern detection (K-means clustering)**: Identify "bad day profiles" by clustering daily feature vectors. Requires sufficient data (30+ days). Add to `backend/backend/analysis/patterns.py`.
- **Schema manager API endpoint**: Currently schema promotion is done via the `/pain-schema` skill using Alembic CLI. A dedicated API endpoint for programmatic promotion can be added later.
- **Directory watcher (Phase C import)**: `backend/backend/importers/watcher.py` — monitor `data/imports/` for new files and auto-import. Requires `watchdog` library.
- **Weather auto-fetch on entry creation**: Currently the `/pain-checkin` skill handles fetching weather via a separate curl call. A backend-side auto-fetch (triggered when a new entry is POSTed without weather data) would be cleaner. Add as middleware or post-save hook in the entries router.

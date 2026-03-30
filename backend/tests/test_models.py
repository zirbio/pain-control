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

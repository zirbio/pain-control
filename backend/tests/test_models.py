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
        PainRecord(location="tobillo_izquierdo", intensity=3, time_of_day="tarde")
    )
    session.add(entry)
    session.commit()

    result = session.query(DailyEntry).first()
    assert result.date == datetime.date(2026, 3, 27)
    assert len(result.pain_records) == 2
    assert result.pain_records[0].location == "lumbar"
    assert result.pain_records[0].intensity == 6
    assert result.pain_records[1].location == "tobillo_izquierdo"


def test_create_full_entry_with_all_record_types(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 27))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.medication_records.append(
        MedicationRecord(name="Captor", dose="75mg tramadol + paracetamol", time_taken="08:00", effectiveness=7)
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
        WeatherRecord(temperature_c=14.5, humidity_pct=78, pressure_hpa=1008.3, pressure_change_hpa=-5.2, conditions="lluvia", location="Madrid")
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
    import pytest
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
    """Deleting a DailyEntry cascades to all child records."""
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 27))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.medication_records.append(MedicationRecord(name="Captor"))
    session.add(entry)
    session.commit()
    entry_id = entry.id

    session.delete(entry)
    session.commit()

    assert session.query(PainRecord).filter(PainRecord.entry_id == entry_id).count() == 0
    assert session.query(MedicationRecord).filter(MedicationRecord.entry_id == entry_id).count() == 0

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


def _base_entry(**overrides):
    """Minimal valid DailyEntryCreate with all required fields."""
    defaults = {
        "date": datetime.date(2026, 3, 27),
        "stretching": False,
        "alcohol": False,
        "heavy_dinner": False,
        "omega3": False,
        "vitamin_d": False,
        "magnesium": False,
        "turmeric": False,
        "mood_score": 5,
    }
    defaults.update(overrides)
    return DailyEntryCreate(**defaults)


def test_daily_entry_create_minimal():
    entry = _base_entry(
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
        )


def test_daily_entry_create_full():
    entry = _base_entry(
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
        _base_entry(mood_score=0)
    with pytest.raises(ValidationError):
        _base_entry(mood_score=11)


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
    entry_min = _base_entry(mood_score=1)
    assert entry_min.mood_score == 1
    entry_max = _base_entry(mood_score=10)
    assert entry_max.mood_score == 10

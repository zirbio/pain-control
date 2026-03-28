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
        medication_records=[MedicationRecordCreate(name="Captor", dose="75mg", time_taken="08:00", effectiveness=7)],
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


def test_pain_record_boundary_values():
    """Boundary values 0 and 10 should be accepted."""
    record_min = PainRecordCreate(location="lumbar", intensity=0)
    assert record_min.intensity == 0
    record_max = PainRecordCreate(location="lumbar", intensity=10)
    assert record_max.intensity == 10


def test_mood_score_boundary_values():
    """Boundary values 1 and 10 should be accepted."""
    mood_min = MoodRecordCreate(score=1)
    assert mood_min.score == 1
    mood_max = MoodRecordCreate(score=10)
    assert mood_max.score == 10

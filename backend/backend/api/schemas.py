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

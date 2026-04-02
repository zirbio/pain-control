import datetime

from pydantic import BaseModel, Field, field_validator

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

    # Day type (auto-detected if omitted; send explicitly for vacation)
    day_type: str | None = None

    # Optional subjective fields
    stress_source: str | None = None
    activity_pain_effect: str | None = None

    @field_validator("day_type")
    @classmethod
    def validate_day_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("workday", "weekend", "vacation"):
            msg = "day_type must be 'workday', 'weekend', or 'vacation'"
            raise ValueError(msg)
        return v

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
    day_type: str | None = None
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

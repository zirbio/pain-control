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
    stretching: bool
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
    stretching: bool | None = None
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
    nutrition_import_records: list[NutritionImportRecordResponse] = []
    workout_records: list[WorkoutRecordResponse] = []
    extras: list[ExtraResponse]

    model_config = {"from_attributes": True}

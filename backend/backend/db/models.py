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
    stretching: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

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


class PainRecord(Base):
    __tablename__ = "pain_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entries.id"), nullable=False, index=True
    )
    location: Mapped[str] = mapped_column(String(50), nullable=False)
    intensity: Mapped[int] = mapped_column(Integer, nullable=False)
    pattern: Mapped[str | None] = mapped_column(String(50))
    time_of_day: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    entry: Mapped["DailyEntry"] = relationship(back_populates="pain_records")


class MedicationRecord(Base):
    __tablename__ = "medication_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entries.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(100))
    time_taken: Mapped[str | None] = mapped_column(String(10))
    effectiveness: Mapped[int | None] = mapped_column(Integer)

    entry: Mapped["DailyEntry"] = relationship(back_populates="medication_records")


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entries.id"), nullable=False, index=True
    )
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
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entries.id"), nullable=False, index=True
    )
    # Core metrics (existing)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    sleep_quality: Mapped[str | None] = mapped_column(Text)
    resting_hr: Mapped[int | None] = mapped_column(Integer)
    hrv_ms: Mapped[float | None] = mapped_column(Float)
    steps: Mapped[int | None] = mapped_column(Integer)
    active_calories: Mapped[int | None] = mapped_column(Integer)
    spo2_pct: Mapped[float | None] = mapped_column(Float)
    raw_data: Mapped[str | None] = mapped_column(Text)
    # Sleep detail
    sleep_rem_hours: Mapped[float | None] = mapped_column(Float)
    # Activity
    distance_km: Mapped[float | None] = mapped_column(Float)
    flights_climbed: Mapped[int | None] = mapped_column(Integer)
    resting_energy_kj: Mapped[float | None] = mapped_column(Float)
    exercise_intensity: Mapped[float | None] = mapped_column(Float)
    # Cardiovascular
    walking_hr_avg: Mapped[int | None] = mapped_column(Integer)
    vo2_max: Mapped[float | None] = mapped_column(Float)
    cardio_recovery: Mapped[float | None] = mapped_column(Float)
    # Walking gait analysis
    step_length_cm: Mapped[float | None] = mapped_column(Float)
    walking_asymmetry_pct: Mapped[float | None] = mapped_column(Float)
    double_support_pct: Mapped[float | None] = mapped_column(Float)
    walking_speed_kmh: Mapped[float | None] = mapped_column(Float)
    # Respiratory
    respiratory_rate: Mapped[float | None] = mapped_column(Float)
    breathing_disturbances: Mapped[float | None] = mapped_column(Float)
    # Body composition
    weight_kg: Mapped[float | None] = mapped_column(Float)
    body_fat_pct: Mapped[float | None] = mapped_column(Float)
    # Environmental
    daylight_min: Mapped[float | None] = mapped_column(Float)

    entry: Mapped["DailyEntry"] = relationship(back_populates="apple_health_records")


class NutritionImportRecord(Base):
    __tablename__ = "nutrition_import_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entries.id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="apple_health")
    # Macronutrients
    calories_kj: Mapped[float | None] = mapped_column(Float)
    protein_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    fat_total_g: Mapped[float | None] = mapped_column(Float)
    fat_saturated_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)
    sugar_g: Mapped[float | None] = mapped_column(Float)
    # Hydration
    water_ml: Mapped[float | None] = mapped_column(Float)
    caffeine_mg: Mapped[float | None] = mapped_column(Float)
    # Minerals
    sodium_mg: Mapped[float | None] = mapped_column(Float)
    potassium_mg: Mapped[float | None] = mapped_column(Float)
    magnesium_mg: Mapped[float | None] = mapped_column(Float)
    calcium_mg: Mapped[float | None] = mapped_column(Float)
    iron_mg: Mapped[float | None] = mapped_column(Float)
    zinc_mg: Mapped[float | None] = mapped_column(Float)
    cholesterol_mg: Mapped[float | None] = mapped_column(Float)
    # Vitamins
    vitamin_a_mcg: Mapped[float | None] = mapped_column(Float)
    vitamin_c_mg: Mapped[float | None] = mapped_column(Float)
    vitamin_d_mcg: Mapped[float | None] = mapped_column(Float)
    vitamin_e_mg: Mapped[float | None] = mapped_column(Float)
    vitamin_k_mcg: Mapped[float | None] = mapped_column(Float)
    vitamin_b6_mg: Mapped[float | None] = mapped_column(Float)
    vitamin_b12_mcg: Mapped[float | None] = mapped_column(Float)
    folate_mcg: Mapped[float | None] = mapped_column(Float)
    niacin_mg: Mapped[float | None] = mapped_column(Float)

    entry: Mapped["DailyEntry"] = relationship(back_populates="nutrition_import_records")


class WorkoutRecord(Base):
    __tablename__ = "workout_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entries.id"), nullable=False, index=True
    )
    workout_type: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    duration_min: Mapped[float | None] = mapped_column(Float)
    active_energy_kj: Mapped[float | None] = mapped_column(Float)
    intensity: Mapped[float | None] = mapped_column(Float)
    max_hr: Mapped[int | None] = mapped_column(Integer)
    avg_hr: Mapped[int | None] = mapped_column(Integer)
    distance_km: Mapped[float | None] = mapped_column(Float)
    steps: Mapped[int | None] = mapped_column(Integer)

    entry: Mapped["DailyEntry"] = relationship(back_populates="workout_records")


class Extra(Base):
    __tablename__ = "extras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("daily_entries.id"), nullable=False, index=True
    )
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

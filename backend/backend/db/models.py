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

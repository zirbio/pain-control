import datetime

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.analysis.reports import generate_report
from backend.db.database import Base
from backend.db.models import (
    ActivityRecord,
    AppleHealthRecord,
    DailyEntry,
    MedicationRecord,
    MoodRecord,
    PainRecord,
    StressRecord,
)


def _make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _populate_full_data(session, n_days=14):
    """Populate database with full data: pain, sleep, activity, medication, mood, stress."""
    np.random.seed(42)
    base_date = datetime.date(2026, 3, 1)
    for i in range(n_days):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i))
        # Pain: two records per day
        entry.pain_records.append(PainRecord(location="lumbar", intensity=np.random.randint(2, 9)))
        entry.pain_records.append(
            PainRecord(location="left_knee", intensity=np.random.randint(1, 6))
        )
        # Medication with effectiveness
        entry.medication_records.append(
            MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=np.random.randint(3, 9))
        )
        # Mood
        entry.mood_records.append(MoodRecord(score=np.random.randint(3, 8)))
        # Activity
        entry.activity_records.append(
            ActivityRecord(type="caminata", duration_min=np.random.randint(15, 60))
        )
        # Stress
        entry.stress_records.append(StressRecord(level=np.random.randint(3, 9)))
        # Apple Health (sleep)
        entry.apple_health_records.append(
            AppleHealthRecord(
                sleep_hours=round(np.random.uniform(5.0, 9.0), 1),
                resting_hr=np.random.randint(55, 75),
                steps=np.random.randint(3000, 12000),
            )
        )
        session.add(entry)
    session.commit()


def test_report_with_full_data(tmp_path):
    """Report with all record types populated should contain all sections."""
    session = _make_session(tmp_path)
    _populate_full_data(session, n_days=14)

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 14),
    )

    # Period section
    assert report["period"]["start"] == "2026-03-01"
    assert report["period"]["end"] == "2026-03-14"
    assert report["period"]["days"] == 14

    # Pain section
    assert "pain" in report
    assert 0 <= report["pain"]["mean"] <= 10
    assert 0 <= report["pain"]["min"] <= 10
    assert 0 <= report["pain"]["max"] <= 10
    assert report["pain"]["good_days"] >= 0
    assert report["pain"]["bad_days"] >= 0
    assert "direction" in report["pain"]["trend"]

    # Sleep section
    assert "sleep" in report
    assert report["sleep"]["min"] <= report["sleep"]["mean"] <= report["sleep"]["max"]

    # Activity section
    assert "activity" in report
    assert report["activity"]["active_days"] == 14  # all days have activity
    assert report["activity"]["total_days"] == 14
    assert report["activity"]["mean_minutes"] is not None

    # Medication section
    assert "medication" in report
    assert 0 <= report["medication"]["mean_effectiveness"] <= 10
    assert report["medication"]["trend"] is not None  # >=3 effectiveness values
    assert "direction" in report["medication"]["trend"]

    # Correlations
    assert "top_correlations" in report
    assert len(report["top_correlations"]) <= 5


def test_report_with_only_pain_data(tmp_path):
    """Report with only pain records should have pain section but not sleep/medication/activity."""
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    for i in range(7):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i))
        entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 7),
    )

    assert "pain" in report
    assert report["pain"]["mean"] == 5.0
    assert report["pain"]["min"] == 5
    assert report["pain"]["max"] == 5

    # Sleep section should be absent (no apple_health_records)
    assert "sleep" not in report

    # Medication section should be absent
    assert "medication" not in report

    # Activity section: present but with 0 active days
    assert "activity" in report
    assert report["activity"]["active_days"] == 0


def test_report_all_pain_max_none(tmp_path):
    """Report where all pain_max values are None (no pain records on entries)."""
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    for i in range(5):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i))
        # No pain records, so pain_max will be None in the DataFrame
        entry.mood_records.append(MoodRecord(score=5))
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 5),
    )

    # pain section should be absent since all pain_max are None (dropna yields empty)
    assert "pain" not in report
    assert "period" in report
    assert report["period"]["days"] == 5


def test_report_medication_below_trend_threshold(tmp_path):
    """Report with exactly 2 medication effectiveness values (below the trend threshold of 3)."""
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    for i in range(5):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i))
        entry.pain_records.append(PainRecord(location="lumbar", intensity=4))
        # Only first 2 days have medication with effectiveness
        if i < 2:
            entry.medication_records.append(
                MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=7)
            )
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 5),
    )

    assert "medication" in report
    assert report["medication"]["mean_effectiveness"] == 7.0
    # Trend should be None because len(eff) < 3
    assert report["medication"]["trend"] is None


def test_report_empty_dataframe(tmp_path):
    """Report with no data at all should return error."""
    session = _make_session(tmp_path)

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 7),
    )

    assert "error" in report
    assert report["error"] == "No data for this period"


def test_report_good_and_bad_days_thresholds(tmp_path):
    """Verify good_days (<=3) and bad_days (>=7) thresholds are correctly applied."""
    session = _make_session(tmp_path)
    base_date = datetime.date(2026, 3, 1)
    # Specific intensities to test thresholds exactly
    intensities = [1, 3, 4, 6, 7, 9, 10, 2, 5, 8]
    # good_days (<=3): 1, 3, 2 => 3 days
    # bad_days (>=7): 7, 9, 10, 8 => 4 days
    for i, intensity in enumerate(intensities):
        entry = DailyEntry(date=base_date + datetime.timedelta(days=i))
        entry.pain_records.append(PainRecord(location="lumbar", intensity=intensity))
        session.add(entry)
    session.commit()

    report = generate_report(
        session,
        start_date=datetime.date(2026, 3, 1),
        end_date=datetime.date(2026, 3, 10),
    )

    assert report["pain"]["good_days"] == 3  # intensities 1, 3, 2
    assert report["pain"]["bad_days"] == 4  # intensities 7, 9, 10, 8

import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.analysis.correlations import (
    build_daily_dataframe,
    compute_lag_correlation,
    compute_pairwise_correlation,
    rank_pain_correlations,
)
from backend.db.database import Base
from backend.db.models import (
    ActivityRecord,
    AppleHealthRecord,
    DailyEntry,
    MedicationRecord,
    MoodRecord,
    NutritionRecord,
    PainRecord,
    StressRecord,
    WeatherRecord,
)


def _sample_dataframe() -> pd.DataFrame:
    """30 days of synthetic data with known correlations."""
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range("2026-03-01", periods=30, freq="D")
    sleep = np.random.normal(7, 1.5, 30).clip(3, 10)
    pain = (10 - sleep + np.random.normal(0, 1, 30)).clip(0, 10)
    pressure = np.random.normal(1013, 5, 30)
    steps = np.random.normal(6000, 2000, 30).clip(0, 15000)
    return pd.DataFrame(
        {
            "date": dates,
            "pain_max": pain.round(0).astype(int),
            "sleep_hours": sleep.round(1),
            "pressure_hpa": pressure.round(1),
            "steps": steps.round(0).astype(int),
        }
    ).set_index("date")


def test_pairwise_correlation_returns_coefficient_and_pvalue():
    df = _sample_dataframe()
    result = compute_pairwise_correlation(df, "pain_max", "sleep_hours")
    assert "coefficient" in result
    assert "p_value" in result
    assert "method" in result
    assert -1 <= result["coefficient"] <= 1
    assert result["coefficient"] < 0


def test_lag_correlation():
    df = _sample_dataframe()
    results = compute_lag_correlation(df, "pain_max", "sleep_hours", max_lag=3)
    assert len(results) == 7
    assert all("lag" in r and "coefficient" in r for r in results)
    lag_0 = next(r for r in results if r["lag"] == 0)
    pairwise = compute_pairwise_correlation(df, "pain_max", "sleep_hours")
    assert abs(lag_0["coefficient"] - pairwise["coefficient"]) < 0.01


def test_rank_pain_correlations():
    df = _sample_dataframe()
    rankings = rank_pain_correlations(df, "pain_max")
    assert len(rankings) > 0
    assert all("variable" in r and "coefficient" in r for r in rankings)
    abs_coeffs = [abs(r["coefficient"]) for r in rankings]
    assert abs_coeffs == sorted(abs_coeffs, reverse=True)


# --- build_daily_dataframe tests ---


def _make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_build_daily_dataframe_all_record_types(tmp_path):
    """Entry with all record types populated should produce all expected columns."""
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=6))
    entry.pain_records.append(PainRecord(location="left_knee", intensity=4))
    entry.medication_records.append(
        MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=7)
    )
    entry.mood_records.append(MoodRecord(score=5, emotions='["cansancio"]'))
    entry.activity_records.append(ActivityRecord(type="caminata", duration_min=30))
    entry.stress_records.append(StressRecord(level=6, source="laboral"))
    entry.nutrition_records.append(NutritionRecord(alcohol=True, caffeine_cups=2, water_liters=1.5))
    entry.weather_records.append(
        WeatherRecord(
            temperature_c=14.5,
            humidity_pct=78,
            pressure_hpa=1008.3,
            pressure_change_hpa=-5.2,
        )
    )
    entry.apple_health_records.append(
        AppleHealthRecord(sleep_hours=6.5, resting_hr=62, hrv_ms=38.5, steps=8432)
    )
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert len(df) == 1
    # Pain columns
    assert df["pain_max"].iloc[0] == 6
    assert df["pain_mean"].iloc[0] == 5.0  # (6+4)/2
    # Medication
    assert df["medication_effectiveness"].iloc[0] == 7.0
    # Mood
    assert df["mood_score"].iloc[0] == 5
    # Activity
    assert df["activity_flag"].iloc[0] == 1
    assert df["activity_minutes"].iloc[0] == 30
    # Stress
    assert df["stress_level"].iloc[0] == 6
    # Nutrition
    assert df["alcohol"].iloc[0] == 1  # True -> int(True) = 1
    assert df["caffeine_cups"].iloc[0] == 2
    assert df["water_liters"].iloc[0] == 1.5
    # Weather
    assert df["temperature_c"].iloc[0] == 14.5
    assert df["humidity_pct"].iloc[0] == 78
    assert df["pressure_hpa"].iloc[0] == 1008.3
    assert df["pressure_change_hpa"].iloc[0] == -5.2
    # Apple Health
    assert df["sleep_hours"].iloc[0] == 6.5
    assert df["resting_hr"].iloc[0] == 62
    assert df["hrv_ms"].iloc[0] == 38.5
    assert df["steps"].iloc[0] == 8432


def test_build_daily_dataframe_empty_pain_records(tmp_path):
    """Entry with no pain records should have pain_max and pain_mean as None."""
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15))
    entry.mood_records.append(MoodRecord(score=5))
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert len(df) == 1
    assert pd.isna(df["pain_max"].iloc[0])
    assert pd.isna(df["pain_mean"].iloc[0])


def test_build_daily_dataframe_multiple_medications_averaged(tmp_path):
    """Multiple medication records with varying effectiveness should be averaged."""
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.medication_records.append(
        MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=8)
    )
    entry.medication_records.append(
        MedicationRecord(name="Paracetamol", dose="500mg", effectiveness=4)
    )
    entry.medication_records.append(
        MedicationRecord(name="Tramadol", dose="50mg", effectiveness=None)
    )
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    # Only effectiveness values that are not None: (8 + 4) / 2 = 6.0
    assert df["medication_effectiveness"].iloc[0] == 6.0


def test_build_daily_dataframe_mood_with_none_emotions(tmp_path):
    """Mood record with None emotions should not crash."""
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15))
    entry.mood_records.append(MoodRecord(score=7, emotions=None))
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert len(df) == 1
    assert df["mood_score"].iloc[0] == 7


# --- constant-value column test for compute_pairwise_correlation ---


def test_pairwise_correlation_constant_column():
    """A column with constant values should return coefficient=None, significant=False."""
    dates = pd.date_range("2026-03-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "pain_max": [3, 5, 7, 4, 6, 8, 2, 5, 7, 3],
            "constant_col": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        },
        index=dates,
    )

    result = compute_pairwise_correlation(df, "pain_max", "constant_col")

    assert result["coefficient"] is None
    assert result["significant"] is False

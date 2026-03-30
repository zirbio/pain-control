import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.analysis.correlations import (
    build_daily_dataframe,
    compute_lag_correlation,
    compute_pairwise_correlation,
    compute_stress_proxy,
    rank_pain_correlations,
)
from backend.db.database import Base
from backend.db.models import (
    AppleHealthRecord,
    DailyEntry,
    MedicationRecord,
    NutritionImportRecord,
    PainRecord,
    WeatherRecord,
    WorkoutRecord,
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


def _make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_build_daily_dataframe_all_fields(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(
        date=datetime.date(2026, 3, 15),
        stretching=True,
        alcohol=True,
        heavy_dinner=False,
        omega3=True,
        vitamin_d=True,
        magnesium=True,
        turmeric=False,
        mood_score=5,
        mood_emotions='["cansancio"]',
        stress_source="laboral",
        activity_pain_effect="mejoró",
    )
    entry.pain_records.append(PainRecord(location="lumbar", intensity=6))
    entry.pain_records.append(PainRecord(location="left_knee", intensity=4))
    entry.medication_records.append(
        MedicationRecord(name="Ibuprofen", dose="400mg", effectiveness=7)
    )
    entry.weather_records.append(
        WeatherRecord(
            temperature_c=14.5,
            humidity_pct=78,
            pressure_hpa=1008.3,
            pressure_change_hpa=-5.2,
        )
    )
    entry.apple_health_records.append(
        AppleHealthRecord(
            sleep_hours=6.5,
            resting_hr=62,
            hrv_ms=38.5,
            steps=8432,
            walking_asymmetry_pct=12.5,
            vo2_max=42.0,
            distance_km=5.3,
        )
    )
    entry.nutrition_import_records.append(
        NutritionImportRecord(
            source="apple_health",
            protein_g=120.5,
            carbs_g=200.0,
            caffeine_mg=400.0,
            vitamin_d_mcg=2.5,
        )
    )
    entry.workout_records.append(
        WorkoutRecord(
            workout_type="Pilates",
            duration_min=58.0,
            active_energy_kj=1200.0,
            intensity=5.2,
            max_hr=141,
            avg_hr=110,
        )
    )
    entry.workout_records.append(
        WorkoutRecord(
            workout_type="Ciclismo",
            duration_min=40.0,
            active_energy_kj=950.0,
            intensity=6.9,
            max_hr=172,
            avg_hr=135,
        )
    )
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert len(df) == 1
    # Pain columns (global)
    assert df["pain_max"].iloc[0] == 6
    assert df["pain_mean"].iloc[0] == 5.0
    # Per-location pain
    assert df["pain_lumbar"].iloc[0] == 6
    assert df["pain_left_knee"].iloc[0] == 4
    # DailyEntry direct fields
    assert df["mood_score"].iloc[0] == 5
    assert df["stretching"].iloc[0] == 1
    assert df["alcohol"].iloc[0] == 1
    assert df["heavy_dinner"].iloc[0] == 0
    assert df["omega3"].iloc[0] == 1
    assert df["vitamin_d"].iloc[0] == 1
    assert df["magnesium"].iloc[0] == 1
    assert df["turmeric"].iloc[0] == 0
    # Medication
    assert df["medication_effectiveness"].iloc[0] == 7.0
    # Weather
    assert df["temperature_c"].iloc[0] == 14.5
    assert df["humidity_pct"].iloc[0] == 78
    # Apple Health
    assert df["sleep_hours"].iloc[0] == 6.5
    assert df["resting_hr"].iloc[0] == 62
    assert df["hrv_ms"].iloc[0] == 38.5
    # Nutrition Import
    assert df["protein_g"].iloc[0] == 120.5
    assert df["caffeine_mg"].iloc[0] == 400.0
    # Workout aggregation
    assert df["workout_count"].iloc[0] == 2
    assert df["workout_total_min"].iloc[0] == 98.0
    assert df["workout_max_hr"].iloc[0] == 172


def test_build_daily_dataframe_per_location_pain(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15), mood_score=5)
    entry.pain_records.append(PainRecord(location="lumbar", intensity=7))
    entry.pain_records.append(PainRecord(location="lumbar", intensity=5))
    entry.pain_records.append(PainRecord(location="tobillo_izq", intensity=3))
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert df["pain_lumbar"].iloc[0] == 7
    assert df["pain_tobillo_izq"].iloc[0] == 3
    assert df["pain_max"].iloc[0] == 7
    assert df["pain_mean"].iloc[0] == 5.0


def test_build_daily_dataframe_empty_pain_records(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15), mood_score=5)
    session.add(entry)
    session.commit()

    df = build_daily_dataframe(session)

    assert len(df) == 1
    assert pd.isna(df["pain_max"].iloc[0])
    assert pd.isna(df["pain_mean"].iloc[0])


def test_build_daily_dataframe_multiple_medications_averaged(tmp_path):
    session = _make_session(tmp_path)
    entry = DailyEntry(date=datetime.date(2026, 3, 15), mood_score=5)
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

    assert df["medication_effectiveness"].iloc[0] == 6.0


def test_stress_proxy_from_hrv():
    import numpy as np

    dates = pd.date_range("2026-03-01", periods=30, freq="D")
    np.random.seed(42)
    hrv = np.random.normal(50, 5, 30)
    hrv[14] = 20  # Notably low HRV day

    df = pd.DataFrame({"hrv_ms": hrv}, index=dates)
    result = compute_stress_proxy(df["hrv_ms"])

    assert len(result) == 30
    assert result.iloc[14] > result.median()
    assert result.min() >= 0
    assert result.max() <= 10


def test_pairwise_correlation_constant_column():
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

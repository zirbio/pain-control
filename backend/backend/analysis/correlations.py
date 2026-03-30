import datetime
import math

import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from backend.db.models import (
    DailyEntry,
    eager_load_options,
)

_APPLE_HEALTH_FIELDS = [
    "sleep_hours",
    "resting_hr",
    "hrv_ms",
    "steps",
    "active_calories",
    "spo2_pct",
    "sleep_rem_hours",
    "distance_km",
    "flights_climbed",
    "resting_energy_kj",
    "exercise_intensity",
    "walking_hr_avg",
    "vo2_max",
    "cardio_recovery",
    "step_length_cm",
    "walking_asymmetry_pct",
    "double_support_pct",
    "walking_speed_kmh",
    "respiratory_rate",
    "breathing_disturbances",
    "weight_kg",
    "body_fat_pct",
    "daylight_min",
]

_NUTRITION_IMPORT_FIELDS = [
    "calories_kj",
    "protein_g",
    "carbs_g",
    "fat_total_g",
    "fat_saturated_g",
    "fiber_g",
    "sugar_g",
    "water_ml",
    "caffeine_mg",
    "sodium_mg",
    "potassium_mg",
    "magnesium_mg",
    "calcium_mg",
    "iron_mg",
    "zinc_mg",
    "cholesterol_mg",
    "vitamin_d_mcg",
    "vitamin_c_mg",
    "vitamin_a_mcg",
    "vitamin_e_mg",
    "vitamin_k_mcg",
    "vitamin_b6_mg",
    "vitamin_b12_mcg",
    "folate_mcg",
    "niacin_mg",
]

_DAILY_ENTRY_BOOL_FIELDS = [
    "stretching",
    "alcohol",
    "heavy_dinner",
    "omega3",
    "vitamin_d",
    "magnesium",
    "turmeric",
]


def compute_stress_proxy(hrv_series: pd.Series, window: int = 30) -> pd.Series:
    """Derive stress proxy (0-10) from HRV: lower HRV relative to baseline = higher stress.

    Uses a rolling window to compute personal baseline. Returns inverted, normalized score.
    """
    baseline = hrv_series.rolling(window=window, min_periods=5, center=True).median()
    # Fill edges with expanding median
    baseline = baseline.fillna(hrv_series.expanding(min_periods=1).median())

    # Deviation: how far below baseline (positive = more stressed)
    deviation = (baseline - hrv_series) / baseline.clip(lower=1)

    # Normalize to 0-10 scale
    stress = 5 + 5 * deviation.clip(lower=-1, upper=1)
    return stress.clip(lower=0, upper=10).round(1)


def build_daily_dataframe(
    db: Session,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> pd.DataFrame:
    """Build a flat daily DataFrame from all record types for analysis."""
    # eager_load_options includes extras; harmless for analysis (just unused)
    query = db.query(DailyEntry).options(*eager_load_options())
    if start_date:
        query = query.filter(DailyEntry.date >= start_date)
    if end_date:
        query = query.filter(DailyEntry.date <= end_date)
    entries = query.order_by(DailyEntry.date).all()

    # Collect all pain locations across all entries for per-location columns
    all_locations: set[str] = set()
    for entry in entries:
        for p in entry.pain_records:
            all_locations.add(p.location)

    rows = []
    for entry in entries:
        row: dict = {"date": entry.date}

        # Boolean fields from DailyEntry → int
        for field in _DAILY_ENTRY_BOOL_FIELDS:
            val = getattr(entry, field, None)
            row[field] = int(val) if val is not None else None

        # Mood from DailyEntry
        row["mood_score"] = entry.mood_score

        # Pain: global aggregates
        if entry.pain_records:
            intensities = [p.intensity for p in entry.pain_records]
            row["pain_max"] = max(intensities)
            row["pain_mean"] = round(sum(intensities) / len(intensities), 1)

            # Per-location pain (max intensity per location)
            loc_max: dict[str, int] = {}
            for p in entry.pain_records:
                loc_max[p.location] = max(loc_max.get(p.location, 0), p.intensity)
            for loc in all_locations:
                row[f"pain_{loc}"] = loc_max.get(loc)
        else:
            row["pain_max"] = None
            row["pain_mean"] = None
            for loc in all_locations:
                row[f"pain_{loc}"] = None

        # Medication effectiveness average
        effs = [m.effectiveness for m in entry.medication_records if m.effectiveness is not None]
        row["medication_effectiveness"] = round(sum(effs) / len(effs), 1) if effs else None

        # First-record extraction for singleton relations
        weather = entry.weather_records[0] if entry.weather_records else None
        for field in ("temperature_c", "humidity_pct", "pressure_hpa", "pressure_change_hpa"):
            row[field] = getattr(weather, field, None)

        ah = entry.apple_health_records[0] if entry.apple_health_records else None
        for field in _APPLE_HEALTH_FIELDS:
            row[field] = getattr(ah, field, None)

        ni = entry.nutrition_import_records[0] if entry.nutrition_import_records else None
        for field in _NUTRITION_IMPORT_FIELDS:
            row[field] = getattr(ni, field, None)

        # Workout aggregation
        workouts = entry.workout_records
        row["workout_count"] = len(workouts)
        row["workout_total_min"] = sum(wr.duration_min or 0 for wr in workouts)
        row["workout_total_energy_kj"] = sum(wr.active_energy_kj or 0 for wr in workouts)
        hrs = [wr.max_hr for wr in workouts if wr.max_hr]
        row["workout_max_hr"] = max(hrs) if hrs else None
        avgs = [wr.avg_hr for wr in workouts if wr.avg_hr]
        row["workout_avg_hr"] = round(sum(avgs) / len(avgs)) if avgs else None
        intensities = [wr.intensity for wr in workouts if wr.intensity is not None]
        row["workout_max_intensity"] = max(intensities) if intensities else None

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    # Compute stress proxy from HRV if available
    if "hrv_ms" in df.columns and df["hrv_ms"].notna().sum() >= 5:
        df["stress_proxy"] = compute_stress_proxy(df["hrv_ms"])

    return df


def _null_pairwise(n: int, method: str) -> dict:
    return {"coefficient": None, "p_value": None, "n": n, "method": method, "significant": False}


def compute_pairwise_correlation(
    df: pd.DataFrame, var_a: str, var_b: str, method: str = "spearman"
) -> dict:
    clean = df[[var_a, var_b]].dropna()
    if len(clean) < 5:
        return _null_pairwise(len(clean), method)

    if method == "spearman":
        coeff, p_value = stats.spearmanr(clean[var_a], clean[var_b])
    else:
        coeff, p_value = stats.pearsonr(clean[var_a], clean[var_b])

    coeff_f = float(coeff)
    p_value_f = float(p_value)
    if math.isnan(coeff_f) or math.isnan(p_value_f):
        return _null_pairwise(len(clean), method)

    return {
        "coefficient": round(coeff_f, 3),
        "p_value": round(p_value_f, 4),
        "n": len(clean),
        "method": method,
        "significant": bool(p_value_f < 0.05),
    }


def _null_result(lag: int, n: int) -> dict:
    return {"lag": lag, "coefficient": None, "p_value": None, "n": n, "significant": False}


def compute_lag_correlation(
    df: pd.DataFrame, target: str, variable: str, max_lag: int = 3
) -> list[dict]:
    """Compute cross-correlation between target and variable at different time offsets."""
    results = []
    for lag in range(-max_lag, max_lag + 1):
        shifted = df[variable].shift(-lag)

        temp_df = pd.DataFrame({target: df[target], variable: shifted}).dropna()
        if len(temp_df) < 5:
            results.append(_null_result(lag, len(temp_df)))
            continue

        coeff, p_value = stats.spearmanr(temp_df[target], temp_df[variable])
        if math.isnan(coeff):
            results.append(_null_result(lag, len(temp_df)))
            continue

        results.append(
            {
                "lag": lag,
                "coefficient": round(float(coeff), 3),
                "p_value": round(float(p_value), 4),
                "n": len(temp_df),
                "significant": bool(p_value < 0.05),
            }
        )
    return results


def rank_pain_correlations(df: pd.DataFrame, pain_column: str = "pain_max") -> list[dict]:
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if pain_column in numeric_cols:
        numeric_cols.remove(pain_column)

    rankings = []
    for col in numeric_cols:
        result = compute_pairwise_correlation(df, pain_column, col)
        if result["coefficient"] is not None:
            rankings.append({"variable": col, **result})

    rankings.sort(key=lambda r: abs(r["coefficient"]), reverse=True)
    return rankings

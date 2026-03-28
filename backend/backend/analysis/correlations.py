import datetime
import math

import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from backend.db.models import (
    DailyEntry,
)


def build_daily_dataframe(
    db: Session,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> pd.DataFrame:
    """Build a flat daily DataFrame from all record types for analysis."""
    query = db.query(DailyEntry)
    if start_date:
        query = query.filter(DailyEntry.date >= start_date)
    if end_date:
        query = query.filter(DailyEntry.date <= end_date)
    entries = query.order_by(DailyEntry.date).all()

    rows = []
    for entry in entries:
        row: dict = {"date": entry.date}

        if entry.pain_records:
            intensities = [p.intensity for p in entry.pain_records]
            row["pain_max"] = max(intensities)
            row["pain_mean"] = round(sum(intensities) / len(intensities), 1)
        else:
            row["pain_max"] = None
            row["pain_mean"] = None

        effs = [m.effectiveness for m in entry.medication_records if m.effectiveness is not None]
        row["medication_effectiveness"] = round(sum(effs) / len(effs), 1) if effs else None

        row["mood_score"] = entry.mood_records[0].score if entry.mood_records else None

        if entry.activity_records:
            row["activity_minutes"] = sum(a.duration_min or 0 for a in entry.activity_records)
            row["activity_flag"] = 1
        else:
            row["activity_minutes"] = 0
            row["activity_flag"] = 0

        row["stress_level"] = entry.stress_records[0].level if entry.stress_records else None

        n = entry.nutrition_records[0] if entry.nutrition_records else None
        row["alcohol"] = int(n.alcohol) if n and n.alcohol is not None else None
        row["caffeine_cups"] = n.caffeine_cups if n else None
        row["water_liters"] = n.water_liters if n else None

        w = entry.weather_records[0] if entry.weather_records else None
        row["temperature_c"] = w.temperature_c if w else None
        row["humidity_pct"] = w.humidity_pct if w else None
        row["pressure_hpa"] = w.pressure_hpa if w else None
        row["pressure_change_hpa"] = w.pressure_change_hpa if w else None

        ah = entry.apple_health_records[0] if entry.apple_health_records else None
        row["sleep_hours"] = ah.sleep_hours if ah else None
        row["resting_hr"] = ah.resting_hr if ah else None
        row["hrv_ms"] = ah.hrv_ms if ah else None
        row["steps"] = ah.steps if ah else None
        row["active_calories"] = ah.active_calories if ah else None
        row["spo2_pct"] = ah.spo2_pct if ah else None

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df


def compute_pairwise_correlation(
    df: pd.DataFrame, var_a: str, var_b: str, method: str = "spearman"
) -> dict:
    clean = df[[var_a, var_b]].dropna()
    if len(clean) < 5:
        return {
            "coefficient": None,
            "p_value": None,
            "n": len(clean),
            "method": method,
            "significant": False,
        }

    if method == "spearman":
        coeff, p_value = stats.spearmanr(clean[var_a], clean[var_b])
    else:
        coeff, p_value = stats.pearsonr(clean[var_a], clean[var_b])

    coeff_f = float(coeff)
    p_value_f = float(p_value)
    if math.isnan(coeff_f) or math.isnan(p_value_f):
        return {
            "coefficient": None,
            "p_value": None,
            "n": len(clean),
            "method": method,
            "significant": False,
        }

    return {
        "coefficient": round(coeff_f, 3),
        "p_value": round(p_value_f, 4),
        "n": len(clean),
        "method": method,
        "significant": bool(p_value_f < 0.05),
    }


def compute_lag_correlation(
    df: pd.DataFrame, target: str, variable: str, max_lag: int = 3
) -> list[dict]:
    results = []
    for lag in range(-max_lag, max_lag + 1):
        shifted = df[variable] if lag == 0 else df[variable].shift(-lag)

        temp_df = pd.DataFrame({target: df[target], variable: shifted}).dropna()
        if len(temp_df) < 5:
            results.append({"lag": lag, "coefficient": None, "p_value": None, "n": len(temp_df)})
            continue

        coeff, p_value = stats.spearmanr(temp_df[target], temp_df[variable])
        if math.isnan(coeff):
            results.append(
                {
                    "lag": lag,
                    "coefficient": None,
                    "p_value": None,
                    "n": len(temp_df),
                    "significant": False,
                }
            )
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


def rank_pain_correlations(
    df: pd.DataFrame, pain_column: str = "pain_max"
) -> list[dict]:
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

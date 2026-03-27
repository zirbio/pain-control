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

        if entry.medication_records:
            effs = [
                m.effectiveness for m in entry.medication_records if m.effectiveness is not None
            ]
            row["medication_effectiveness"] = round(sum(effs) / len(effs), 1) if effs else None
        else:
            row["medication_effectiveness"] = None

        if entry.mood_records:
            row["mood_score"] = entry.mood_records[0].score
        else:
            row["mood_score"] = None

        if entry.activity_records:
            row["activity_minutes"] = sum(a.duration_min or 0 for a in entry.activity_records)
            row["activity_flag"] = 1
        else:
            row["activity_minutes"] = 0
            row["activity_flag"] = 0

        if entry.stress_records:
            row["stress_level"] = entry.stress_records[0].level
        else:
            row["stress_level"] = None

        if entry.nutrition_records:
            n = entry.nutrition_records[0]
            row["alcohol"] = int(n.alcohol) if n.alcohol is not None else None
            row["caffeine_cups"] = n.caffeine_cups
            row["water_liters"] = n.water_liters
        else:
            row["alcohol"] = None
            row["caffeine_cups"] = None
            row["water_liters"] = None

        if entry.weather_records:
            w = entry.weather_records[0]
            row["temperature_c"] = w.temperature_c
            row["humidity_pct"] = w.humidity_pct
            row["pressure_hpa"] = w.pressure_hpa
            row["pressure_change_hpa"] = w.pressure_change_hpa
        else:
            row["temperature_c"] = None
            row["humidity_pct"] = None
            row["pressure_hpa"] = None
            row["pressure_change_hpa"] = None

        if entry.apple_health_records:
            ah = entry.apple_health_records[0]
            row["sleep_hours"] = ah.sleep_hours
            row["resting_hr"] = ah.resting_hr
            row["hrv_ms"] = ah.hrv_ms
            row["steps"] = ah.steps
            row["active_calories"] = ah.active_calories
            row["spo2_pct"] = ah.spo2_pct
        else:
            row["sleep_hours"] = None
            row["resting_hr"] = None
            row["hrv_ms"] = None
            row["steps"] = None
            row["active_calories"] = None
            row["spo2_pct"] = None

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
            rankings.append(
                {
                    "variable": col,
                    "coefficient": result["coefficient"],
                    "p_value": result["p_value"],
                    "n": result["n"],
                    "significant": result["significant"],
                }
            )

    rankings.sort(key=lambda r: abs(r["coefficient"]), reverse=True)
    return rankings

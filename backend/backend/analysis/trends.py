import numpy as np
import pandas as pd
from scipy import stats


def compute_moving_average(df: pd.DataFrame, column: str, window: int = 7) -> pd.DataFrame:
    result = df.copy()
    result[f"{column}_ma{window}"] = result[column].rolling(window=window).mean().round(1)
    return result


def compute_trend_direction(df: pd.DataFrame, column: str) -> dict:
    clean = df[[column]].dropna()
    if len(clean) < 3:
        return {"direction": "insufficient_data", "slope": 0, "r_squared": 0}

    x = np.arange(len(clean))
    y = clean[column].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    if np.isnan(p_value) or p_value > 0.05:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    return {
        "direction": direction,
        "slope": round(float(slope), 4),
        "r_squared": round(float(r_value**2), 3),
        "p_value": round(float(p_value), 4),
    }


def compare_periods(
    df: pd.DataFrame,
    column: str,
    period_a_start: str,
    period_a_end: str,
    period_b_start: str,
    period_b_end: str,
) -> dict:
    a = df.loc[period_a_start:period_a_end, column].dropna()
    b = df.loc[period_b_start:period_b_end, column].dropna()

    a_mean = a.mean() if len(a) > 0 else None
    b_mean = b.mean() if len(b) > 0 else None

    if pd.isna(a_mean) or pd.isna(b_mean):
        return {
            "period_a_mean": None,
            "period_b_mean": None,
            "difference": None,
            "p_value": None,
            "significant": False,
            "n_a": len(a),
            "n_b": len(b),
        }

    if len(a) < 3 or len(b) < 3:
        return {
            "period_a_mean": round(float(a_mean), 1),
            "period_b_mean": round(float(b_mean), 1),
            "difference": None,
            "p_value": None,
            "significant": False,
            "n_a": len(a),
            "n_b": len(b),
        }

    stat, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")

    return {
        "period_a_mean": round(float(a_mean), 1),
        "period_b_mean": round(float(b_mean), 1),
        "difference": round(float(b_mean - a_mean), 1),
        "p_value": round(float(p_value), 4),
        "significant": p_value < 0.05,
        "n_a": len(a),
        "n_b": len(b),
    }

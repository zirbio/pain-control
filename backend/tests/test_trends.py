import numpy as np
import pandas as pd

from backend.analysis.trends import (
    compare_periods,
    compute_moving_average,
    compute_trend_direction,
)


def _sample_df():
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    np.random.seed(42)
    pain = (np.linspace(6, 4, 60) + np.random.normal(0, 0.5, 60)).clip(0, 10).round(1)
    return pd.DataFrame({"pain_max": pain}, index=dates)


def test_moving_average():
    df = _sample_df()
    result = compute_moving_average(df, "pain_max", window=7)
    assert "pain_max_ma7" in result.columns
    assert result["pain_max_ma7"].iloc[6] is not None
    assert pd.isna(result["pain_max_ma7"].iloc[0])


def test_trend_direction_detects_decrease():
    df = _sample_df()
    trend = compute_trend_direction(df, "pain_max")
    assert trend["direction"] == "decreasing"
    assert trend["slope"] < 0


def test_compare_periods():
    df = _sample_df()
    result = compare_periods(
        df,
        "pain_max",
        period_a_start="2026-01-01",
        period_a_end="2026-01-30",
        period_b_start="2026-02-01",
        period_b_end="2026-03-01",
    )
    assert "period_a_mean" in result
    assert "period_b_mean" in result
    assert "difference" in result
    assert "p_value" in result
    assert result["period_b_mean"] < result["period_a_mean"]

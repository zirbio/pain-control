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


# --- compute_trend_direction additional tests ---


def test_trend_direction_fewer_than_3_nonull():
    """Column with fewer than 3 non-null values should return insufficient_data."""
    dates = pd.date_range("2026-03-01", periods=5, freq="D")
    df = pd.DataFrame(
        {"pain_max": [4.0, np.nan, np.nan, np.nan, np.nan]},
        index=dates,
    )

    trend = compute_trend_direction(df, "pain_max")
    assert trend["direction"] == "insufficient_data"
    assert trend["slope"] == 0
    assert trend["r_squared"] == 0


def test_trend_direction_flat_values():
    """Flat constant values should be classified as 'stable'."""
    dates = pd.date_range("2026-03-01", periods=10, freq="D")
    df = pd.DataFrame({"pain_max": [5.0] * 10}, index=dates)

    trend = compute_trend_direction(df, "pain_max")
    assert trend["direction"] == "stable"
    assert trend["slope"] == 0.0


def test_trend_direction_increasing():
    """Clearly increasing values should return increasing."""
    dates = pd.date_range("2026-03-01", periods=7, freq="D")
    df = pd.DataFrame(
        {"pain_max": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]},
        index=dates,
    )

    trend = compute_trend_direction(df, "pain_max")
    assert trend["direction"] == "increasing"
    assert trend["slope"] > 0


def test_trend_direction_all_nan():
    """Column with all NaN should return insufficient_data."""
    dates = pd.date_range("2026-03-01", periods=5, freq="D")
    df = pd.DataFrame({"pain_max": [np.nan] * 5}, index=dates)

    trend = compute_trend_direction(df, "pain_max")
    assert trend["direction"] == "insufficient_data"


# --- compare_periods edge case tests ---


def test_compare_periods_zero_data_period_a():
    """Period A with 0 data points should return None values (not NaN)."""
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    np.random.seed(42)
    pain = np.random.normal(5, 1, 60).clip(0, 10).round(1)
    df = pd.DataFrame({"pain_max": pain}, index=dates)

    result = compare_periods(
        df,
        "pain_max",
        # Period A: a date range with no data
        period_a_start="2025-01-01",
        period_a_end="2025-01-31",
        # Period B: has data
        period_b_start="2026-01-01",
        period_b_end="2026-01-30",
    )

    assert result["period_a_mean"] is None
    assert result["n_a"] == 0
    assert result["difference"] is None
    assert result["p_value"] is None
    assert result["significant"] is False


def test_compare_periods_identical_data():
    """Both periods with identical data should return significant=False."""
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    # Perfectly identical values across both periods
    values = [5.0] * 60
    df = pd.DataFrame({"pain_max": values}, index=dates)

    result = compare_periods(
        df,
        "pain_max",
        period_a_start="2026-01-01",
        period_a_end="2026-01-30",
        period_b_start="2026-02-01",
        period_b_end="2026-03-01",
    )

    assert result["significant"] == False  # noqa: E712 — np.bool_ vs bool
    assert result["difference"] == 0.0


def test_compare_periods_fewer_than_3_data_points():
    """Periods with fewer than 3 data points each should return partial results."""
    dates = pd.date_range("2026-01-01", periods=4, freq="D")
    df = pd.DataFrame({"pain_max": [5.0, 6.0, 7.0, 8.0]}, index=dates)

    result = compare_periods(
        df,
        "pain_max",
        # Period A: only 2 data points
        period_a_start="2026-01-01",
        period_a_end="2026-01-02",
        # Period B: only 2 data points
        period_b_start="2026-01-03",
        period_b_end="2026-01-04",
    )

    # With fewer than 3 points, difference and p_value should be None
    assert result["difference"] is None
    assert result["p_value"] is None
    assert result["significant"] is False
    assert result["n_a"] == 2
    assert result["n_b"] == 2
    # But means should still be calculated since data exists
    assert result["period_a_mean"] == 5.5
    assert result["period_b_mean"] == 7.5

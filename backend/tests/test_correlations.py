import pandas as pd

from backend.analysis.correlations import (
    compute_lag_correlation,
    compute_pairwise_correlation,
    rank_pain_correlations,
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

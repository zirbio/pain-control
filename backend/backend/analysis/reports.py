import datetime

from sqlalchemy.orm import Session

from backend.analysis.correlations import build_daily_dataframe, rank_pain_correlations
from backend.analysis.trends import compute_trend_direction


def generate_report(
    db: Session,
    start_date: datetime.date,
    end_date: datetime.date,
) -> dict:
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty:
        return {"error": "No data for this period"}

    report: dict = {
        "period": {"start": str(start_date), "end": str(end_date), "days": len(df)},
    }

    if "pain_max" in df.columns:
        pain = df["pain_max"].dropna()
        if len(pain) > 0:
            report["pain"] = {
                "mean": round(float(pain.mean()), 1),
                "min": int(pain.min()),
                "max": int(pain.max()),
                "good_days": int((pain <= 3).sum()),
                "bad_days": int((pain >= 7).sum()),
                "trend": compute_trend_direction(df, "pain_max"),
            }

    if "sleep_hours" in df.columns:
        sleep = df["sleep_hours"].dropna()
        if len(sleep) > 0:
            report["sleep"] = {
                "mean": round(float(sleep.mean()), 1),
                "min": round(float(sleep.min()), 1),
                "max": round(float(sleep.max()), 1),
            }

    if "activity_flag" in df.columns:
        report["activity"] = {
            "active_days": int(df["activity_flag"].sum()),
            "total_days": len(df),
            "mean_minutes": round(float(df["activity_minutes"].mean()), 0)
            if "activity_minutes" in df.columns
            else None,
        }

    if "medication_effectiveness" in df.columns:
        eff = df["medication_effectiveness"].dropna()
        if len(eff) > 0:
            report["medication"] = {
                "mean_effectiveness": round(float(eff.mean()), 1),
                "trend": compute_trend_direction(df, "medication_effectiveness")
                if len(eff) >= 3
                else None,
            }

    if "pain_max" in df.columns:
        report["top_correlations"] = rank_pain_correlations(df, "pain_max")[:5]

    return report

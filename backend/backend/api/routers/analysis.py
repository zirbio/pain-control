import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.analysis.correlations import (
    build_daily_dataframe,
    compute_lag_correlation,
    compute_pairwise_correlation,
    rank_pain_correlations,
)
from backend.analysis.reports import generate_report

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/correlation")
def get_correlation(
    var_a: str = Query(...),
    var_b: str = Query(...),
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty or var_a not in df.columns or var_b not in df.columns:
        return {"error": "Insufficient data or invalid variable names"}
    return compute_pairwise_correlation(df, var_a, var_b)


@router.get("/lag-correlation")
def get_lag_correlation(
    target: str = Query(...),
    variable: str = Query(...),
    max_lag: int = Query(default=3, ge=1, le=7),
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty or target not in df.columns or variable not in df.columns:
        return {"error": "Insufficient data or invalid variable names"}
    return compute_lag_correlation(df, target, variable, max_lag=max_lag)


@router.get("/rankings")
def get_rankings(
    pain_column: str = Query(default="pain_max"),
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    df = build_daily_dataframe(db, start_date=start_date, end_date=end_date)
    if df.empty:
        return []
    return rank_pain_correlations(df, pain_column)


@router.get("/report")
def get_report(
    start_date: datetime.date = Query(...),
    end_date: datetime.date = Query(...),
    db: Session = Depends(get_db),
):
    return generate_report(db, start_date, end_date)

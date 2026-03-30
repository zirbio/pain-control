import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.schemas import DailyEntryCreate, DailyEntryResponse
from backend.db.models import (
    DailyEntry,
    Extra,
    MedicationRecord,
    PainRecord,
    eager_load_options,
)

router = APIRouter(prefix="/api/entries", tags=["entries"])


_DIRECT_FIELDS = (
    "stretching",
    "alcohol",
    "heavy_dinner",
    "omega3",
    "vitamin_d",
    "magnesium",
    "turmeric",
    "mood_score",
    "stress_source",
    "activity_pain_effect",
)


def _populate_entry(entry: DailyEntry, data: DailyEntryCreate) -> None:
    """Populate a DailyEntry with data from the create schema."""
    for field in _DIRECT_FIELDS:
        setattr(entry, field, getattr(data, field))
    entry.mood_emotions = json.dumps(data.mood_emotions) if data.mood_emotions else None

    entry.pain_records = [PainRecord(**r.model_dump()) for r in data.pain_records]
    entry.medication_records = [MedicationRecord(**r.model_dump()) for r in data.medication_records]
    entry.extras = [
        Extra(key=e.key, value=e.value, value_type=e.value_type, first_seen=data.date)
        for e in data.extras
    ]


@router.post("", response_model=DailyEntryResponse)
def create_or_update_entry(
    data: DailyEntryCreate, response: Response, db: Session = Depends(get_db)
):
    existing = db.query(DailyEntry).filter(DailyEntry.date == data.date).first()
    if existing:
        _populate_entry(existing, data)
        db.commit()
        db.refresh(existing)
        response.status_code = 200
        return existing

    entry = DailyEntry(date=data.date)
    _populate_entry(entry, data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    response.status_code = 201
    return entry


@router.get("/{date}", response_model=DailyEntryResponse)
def get_entry_by_date(date: datetime.date, db: Session = Depends(get_db)):
    entry = (
        db.query(DailyEntry).options(*eager_load_options()).filter(DailyEntry.date == date).first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail=f"No entry for {date}")
    return entry


@router.get("", response_model=list[DailyEntryResponse])
def list_entries(
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    limit: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    query = db.query(DailyEntry).options(*eager_load_options())
    if start_date:
        query = query.filter(DailyEntry.date >= start_date)
    if end_date:
        query = query.filter(DailyEntry.date <= end_date)
    return query.order_by(DailyEntry.date.desc()).limit(limit).all()


@router.delete("/{date}", status_code=204)
def delete_entry(date: datetime.date, db: Session = Depends(get_db)):
    entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"No entry for {date}")
    db.delete(entry)
    db.commit()

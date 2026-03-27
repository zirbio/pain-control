import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.schemas import DailyEntryCreate, DailyEntryResponse
from backend.db.models import (
    ActivityRecord,
    AppleHealthRecord,
    DailyEntry,
    Extra,
    MedicationRecord,
    MoodRecord,
    NutritionRecord,
    PainRecord,
    StressRecord,
    WeatherRecord,
)

router = APIRouter(prefix="/api/entries", tags=["entries"])


def _populate_entry(entry: DailyEntry, data: DailyEntryCreate) -> None:
    """Populate a DailyEntry with records from the create schema."""
    entry.pain_records = [
        PainRecord(**r.model_dump()) for r in data.pain_records
    ]
    entry.medication_records = [
        MedicationRecord(**r.model_dump()) for r in data.medication_records
    ]
    entry.mood_records = [
        MoodRecord(
            score=r.score,
            emotions=json.dumps(r.emotions) if r.emotions else None,
            notes=r.notes,
        )
        for r in data.mood_records
    ]
    entry.activity_records = [
        ActivityRecord(**r.model_dump()) for r in data.activity_records
    ]
    entry.stress_records = [
        StressRecord(**r.model_dump()) for r in data.stress_records
    ]
    entry.nutrition_records = [
        NutritionRecord(
            meals=json.dumps(r.meals) if r.meals else None,
            alcohol=r.alcohol,
            caffeine_cups=r.caffeine_cups,
            water_liters=r.water_liters,
            notes=r.notes,
        )
        for r in data.nutrition_records
    ]
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
    entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
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
    query = db.query(DailyEntry)
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

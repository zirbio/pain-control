from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.core.config import get_settings
from backend.db.models import (
    AppleHealthRecord,
    DailyEntry,
    NutritionImportRecord,
    WorkoutRecord,
)
from backend.importers.apple_health import (
    AppleHealthImporter,
    DailyImportData,
    WorkoutData,
)

router = APIRouter(prefix="/api/imports", tags=["imports"])

# Fields from dataclasses that don't map to ORM columns
_HEALTH_EXCLUDE = {"date", "sleep_quality", "raw_data"}
_NUTRITION_EXCLUDE = {"date"}
_WORKOUT_EXCLUDE = {"date"}


def get_imports_dir() -> str:
    return get_settings().IMPORTS_DIR


def _get_or_create_entry(db: Session, date) -> DailyEntry:
    entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
    if not entry:
        entry = DailyEntry(date=date)
        db.add(entry)
        db.flush()
    return entry


def _dataclass_to_dict(obj, exclude: set[str]) -> dict:
    return {k: v for k, v in asdict(obj).items() if k not in exclude}


def _persist_health_data(
    db: Session,
    daily_data: dict,
) -> int:
    total_days = 0
    for date, raw_data in daily_data.items():
        health_data = raw_data.health if isinstance(raw_data, DailyImportData) else raw_data
        entry = _get_or_create_entry(db, date)

        db.query(AppleHealthRecord).filter(AppleHealthRecord.entry_id == entry.id).delete()
        db.add(
            AppleHealthRecord(
                entry_id=entry.id,
                **_dataclass_to_dict(health_data, _HEALTH_EXCLUDE),
            )
        )

        if isinstance(raw_data, DailyImportData) and raw_data.nutrition:
            db.query(NutritionImportRecord).filter(
                NutritionImportRecord.entry_id == entry.id
            ).delete()
            db.add(
                NutritionImportRecord(
                    entry_id=entry.id,
                    source="apple_health",
                    **_dataclass_to_dict(raw_data.nutrition, _NUTRITION_EXCLUDE),
                )
            )

        total_days += 1
    return total_days


def _persist_workout_data(
    db: Session,
    workouts: list[WorkoutData],
) -> int:
    by_date: dict = defaultdict(list)
    for w in workouts:
        by_date[w.date].append(w)

    total = 0
    for date, day_workouts in by_date.items():
        entry = _get_or_create_entry(db, date)
        db.query(WorkoutRecord).filter(WorkoutRecord.entry_id == entry.id).delete()

        for w in day_workouts:
            db.add(
                WorkoutRecord(
                    entry_id=entry.id,
                    **_dataclass_to_dict(w, _WORKOUT_EXCLUDE),
                )
            )
            total += 1
    return total


@router.post("/apple-health")
def import_apple_health(db: Session = Depends(get_db)):
    imports_dir = Path(get_imports_dir())
    if not imports_dir.exists():
        return {"files_processed": 0, "days_imported": 0, "errors": ["imports directory not found"]}

    xml_files = list(imports_dir.glob("*.xml"))
    csv_files = list(imports_dir.glob("HealthAutoExport-*.csv"))
    workout_files = list(imports_dir.glob("Workouts-*.csv"))
    health_files = xml_files + csv_files

    if not health_files and not workout_files:
        return {"files_processed": 0, "days_imported": 0, "workouts_imported": 0, "errors": []}

    importer = AppleHealthImporter()
    total_days = 0
    total_workouts = 0
    errors = []

    for file in health_files:
        try:
            if file.suffix == ".xml":
                daily_data = importer.parse_xml(file)
            else:
                daily_data = importer.parse_csv(file)

            total_days += _persist_health_data(db, daily_data)
            db.commit()
        except Exception as e:
            db.rollback()
            errors.append(f"{file.name}: {e}")

    for file in workout_files:
        try:
            workouts = importer.parse_workouts_csv(file)
            total_workouts += _persist_workout_data(db, workouts)
            db.commit()
        except Exception as e:
            db.rollback()
            errors.append(f"{file.name}: {e}")

    return {
        "files_processed": len(health_files) + len(workout_files),
        "days_imported": total_days,
        "workouts_imported": total_workouts,
        "errors": errors,
    }

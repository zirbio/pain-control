from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.core.config import get_settings
from backend.db.models import AppleHealthRecord, DailyEntry
from backend.importers.apple_health import AppleHealthImporter

router = APIRouter(prefix="/api/imports", tags=["imports"])


def get_imports_dir() -> str:
    return get_settings().IMPORTS_DIR


@router.post("/apple-health")
def import_apple_health(db: Session = Depends(get_db)):
    imports_dir = Path(get_imports_dir())
    if not imports_dir.exists():
        return {"files_processed": 0, "days_imported": 0, "errors": ["imports directory not found"]}

    xml_files = list(imports_dir.glob("*.xml"))
    if not xml_files:
        return {"files_processed": 0, "days_imported": 0, "errors": []}

    importer = AppleHealthImporter()
    total_days = 0
    errors = []

    for xml_file in xml_files:
        try:
            daily_data = importer.parse_xml(xml_file)
            for date, health_data in daily_data.items():
                entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
                if not entry:
                    entry = DailyEntry(date=date)
                    db.add(entry)
                    db.flush()

                db.query(AppleHealthRecord).filter(
                    AppleHealthRecord.entry_id == entry.id
                ).delete()

                record = AppleHealthRecord(
                    entry_id=entry.id,
                    sleep_hours=health_data.sleep_hours,
                    resting_hr=health_data.resting_hr,
                    hrv_ms=health_data.hrv_ms,
                    steps=health_data.steps,
                    active_calories=health_data.active_calories,
                    spo2_pct=health_data.spo2_pct,
                )
                db.add(record)
                total_days += 1

            db.commit()
        except Exception as e:
            errors.append(f"{xml_file.name}: {e}")

    return {
        "files_processed": len(xml_files),
        "days_imported": total_days,
        "errors": errors,
    }

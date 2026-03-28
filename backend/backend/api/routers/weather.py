import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.core.config import get_settings
from backend.db.models import DailyEntry, WeatherRecord
from backend.importers.geocoding import geocode_city
from backend.importers.weather import WeatherImporter

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.post("/{date}")
def fetch_and_save_weather(
    date: datetime.date,
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    location: str | None = Query(default=None),
    city: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()

    # Resolve location: city name → geocode, or use params, or use defaults
    resolved_lat = lat if lat is not None else settings.WEATHER_LAT
    resolved_lon = lon if lon is not None else settings.WEATHER_LON
    resolved_location = location or settings.WEATHER_LOCATION

    if city:
        geo = geocode_city(city)
        if geo:
            resolved_lat, resolved_lon, resolved_location = geo
        else:
            raise HTTPException(status_code=404, detail=f"City not found: {city}")

    importer = WeatherImporter(lat=resolved_lat, lon=resolved_lon, location=resolved_location)

    try:
        weather = importer.fetch_date(date)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather API error: {e}") from e

    # Compute pressure change vs yesterday
    yesterday = date - datetime.timedelta(days=1)
    yesterday_record = (
        db.query(WeatherRecord).join(DailyEntry).filter(DailyEntry.date == yesterday).first()
    )
    if yesterday_record and yesterday_record.pressure_hpa:
        weather.pressure_change_hpa = importer.compute_pressure_change(
            weather.pressure_hpa, yesterday_record.pressure_hpa
        )

    # Upsert: get or create DailyEntry
    entry = db.query(DailyEntry).filter(DailyEntry.date == date).first()
    if not entry:
        entry = DailyEntry(date=date)
        db.add(entry)
        db.flush()

    # Remove existing weather records for this day
    db.query(WeatherRecord).filter(WeatherRecord.entry_id == entry.id).delete()

    record = WeatherRecord(
        entry_id=entry.id,
        temperature_c=weather.temperature_c,
        humidity_pct=weather.humidity_pct,
        pressure_hpa=weather.pressure_hpa,
        pressure_change_hpa=weather.pressure_change_hpa,
        conditions=weather.conditions,
        location=weather.location,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "date": str(date),
        "temperature_c": record.temperature_c,
        "humidity_pct": record.humidity_pct,
        "pressure_hpa": record.pressure_hpa,
        "pressure_change_hpa": record.pressure_change_hpa,
        "conditions": record.conditions,
        "location": record.location,
    }

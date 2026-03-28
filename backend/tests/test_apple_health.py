import datetime
from pathlib import Path

from backend.importers.apple_health import AppleHealthImporter, DailyHealthData

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_xml_extracts_daily_data():
    importer = AppleHealthImporter()
    results = importer.parse_xml(FIXTURES_DIR / "sample_health_export.xml")
    assert len(results) >= 1
    day = results[datetime.date(2026, 3, 27)]
    assert isinstance(day, DailyHealthData)
    assert day.steps == 8432
    assert day.resting_hr == 58
    assert abs(day.hrv_ms - 38.5) < 0.1
    assert day.active_calories == 340
    assert day.spo2_pct is not None
    assert abs(day.spo2_pct - 97.0) < 0.1


def test_parse_xml_computes_sleep_hours():
    importer = AppleHealthImporter()
    results = importer.parse_xml(FIXTURES_DIR / "sample_health_export.xml")
    day = results[datetime.date(2026, 3, 27)]
    # Sleep: 23:30→02:00 (2.5h) + 02:00→04:00 (2h) + 04:00→06:00 (2h) = 6.5h
    assert day.sleep_hours is not None
    assert abs(day.sleep_hours - 6.5) < 0.1


def test_parse_xml_empty_file(tmp_path):
    xml_file = tmp_path / "empty.xml"
    xml_file.write_text('<?xml version="1.0"?><HealthData></HealthData>')
    importer = AppleHealthImporter()
    results = importer.parse_xml(xml_file)
    assert len(results) == 0

import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DailyHealthData:
    date: datetime.date
    sleep_hours: float | None = None
    sleep_quality: str | None = None
    resting_hr: int | None = None
    hrv_ms: float | None = None
    steps: int | None = None
    active_calories: int | None = None
    spo2_pct: float | None = None


QUANTITY_TYPES = {
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_hr",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "hrv_ms",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_calories",
    "HKQuantityTypeIdentifierOxygenSaturation": "spo2_pct",
}

SLEEP_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"
ASLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepDeep",
    "HKCategoryValueSleepAnalysisAsleepREM",
    "HKCategoryValueSleepAnalysisAsleepUnspecified",
    "HKCategoryValueSleepAnalysisAsleep",
}


def _parse_date(date_str: str) -> datetime.date:
    return datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S").date()


def _parse_datetime(date_str: str) -> datetime.datetime:
    return datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")


class AppleHealthImporter:
    def parse_xml(self, xml_path: Path) -> dict[datetime.date, DailyHealthData]:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        daily_steps: dict[datetime.date, int] = defaultdict(int)
        daily_calories: dict[datetime.date, int] = defaultdict(int)
        daily_resting_hr: dict[datetime.date, list[float]] = defaultdict(list)
        daily_hrv: dict[datetime.date, list[float]] = defaultdict(list)
        daily_spo2: dict[datetime.date, list[float]] = defaultdict(list)
        daily_sleep_minutes: dict[datetime.date, float] = defaultdict(float)
        all_dates: set[datetime.date] = set()

        for record in root.iter("Record"):
            record_type = record.get("type", "")
            start_str = record.get("startDate", "")
            end_str = record.get("endDate", "")
            value_str = record.get("value", "")

            if not start_str:
                continue

            date = _parse_date(start_str)
            all_dates.add(date)

            if record_type == "HKQuantityTypeIdentifierStepCount":
                daily_steps[date] += int(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierActiveEnergyBurned":
                daily_calories[date] += int(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierRestingHeartRate":
                daily_resting_hr[date].append(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierHeartRateVariabilitySDNN":
                daily_hrv[date].append(float(value_str))
            elif record_type == "HKQuantityTypeIdentifierOxygenSaturation":
                pct = float(value_str)
                if pct <= 1.0:
                    pct *= 100
                daily_spo2[date].append(pct)
            elif record_type == SLEEP_TYPE and value_str in ASLEEP_VALUES and end_str:
                start_dt = _parse_datetime(start_str)
                end_dt = _parse_datetime(end_str)
                minutes = (end_dt - start_dt).total_seconds() / 60
                sleep_date = _parse_date(end_str)
                daily_sleep_minutes[sleep_date] += minutes
                all_dates.add(sleep_date)

        results: dict[datetime.date, DailyHealthData] = {}
        for date in sorted(all_dates):
            data = DailyHealthData(date=date)
            if date in daily_steps:
                data.steps = daily_steps[date]
            if date in daily_calories:
                data.active_calories = daily_calories[date]
            if date in daily_resting_hr:
                data.resting_hr = int(sum(daily_resting_hr[date]) / len(daily_resting_hr[date]))
            if date in daily_hrv:
                data.hrv_ms = round(sum(daily_hrv[date]) / len(daily_hrv[date]), 1)
            if date in daily_spo2:
                data.spo2_pct = round(sum(daily_spo2[date]) / len(daily_spo2[date]), 1)
            if date in daily_sleep_minutes:
                data.sleep_hours = round(daily_sleep_minutes[date] / 60, 1)
            results[date] = data

        return results

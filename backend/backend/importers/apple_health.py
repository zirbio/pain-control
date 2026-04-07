import csv
import datetime
import logging
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

WORKOUT_TYPE_MAP: dict[str, str] = {
    "Entrenamiento de Fuerza Funcional": "Rehabilitation",
    "Pilates": "Pilates",
    "Interior Ciclismo": "Indoor Cycling",
    "Caminata": "Walking",
    "Yoga": "Yoga",
    "Natación": "Swimming",
    "Ciclismo": "Cycling",
    "Elíptica": "Elliptical",
    "Estiramientos": "Stretching",
    "Golf": "Golf",
}

# Workout CSV column maps. Health Auto Export changed format around 2026-03-28:
# v1 (Spanish, single combined file) → v2 (English, one file per day, separate iCloud folder).
# Both formats use identical "Start", "End", "Duration" column names.
WORKOUT_COLUMNS_V1: dict[str, str] = {
    "type": "Workout Type",
    "active_energy_kj": "Energía Activa (kJ)",
    "intensity": "Intensidad (kcal/hr·kg)",
    "max_hr": "Frecuencia Cardíaca Máxima (bpm)",
    "avg_hr": "Frecuencia Cardíaca Promedio (bpm)",
    "distance_km": "Distancia (km)",
    "steps": "Conteo de Pasos",
}

WORKOUT_COLUMNS_V2: dict[str, str] = {
    "type": "Type",
    "active_energy_kj": "Active Energy (kJ)",
    # v2 dropped the "Intensidad" column entirely.
    "max_hr": "Max Heart Rate (bpm)",
    "avg_hr": "Avg Heart Rate (bpm)",
    "distance_km": "Distance (km)",
    "steps": "Step Count (count)",
}


def normalize_workout_type(raw_type: str) -> str:
    normalized = WORKOUT_TYPE_MAP.get(raw_type)
    if normalized is None:
        logger.warning("Unknown workout type: '%s' — storing as-is", raw_type)
        return raw_type
    return normalized


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
    sleep_rem_hours: float | None = None
    distance_km: float | None = None
    flights_climbed: int | None = None
    resting_energy_kj: float | None = None
    exercise_intensity: float | None = None
    walking_hr_avg: int | None = None
    vo2_max: float | None = None
    cardio_recovery: float | None = None
    step_length_cm: float | None = None
    walking_asymmetry_pct: float | None = None
    double_support_pct: float | None = None
    walking_speed_kmh: float | None = None
    respiratory_rate: float | None = None
    breathing_disturbances: float | None = None
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    daylight_min: float | None = None


@dataclass
class DailyNutritionData:
    date: datetime.date
    calories_kj: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_total_g: float | None = None
    fat_saturated_g: float | None = None
    fiber_g: float | None = None
    sugar_g: float | None = None
    water_ml: float | None = None
    caffeine_mg: float | None = None
    sodium_mg: float | None = None
    potassium_mg: float | None = None
    magnesium_mg: float | None = None
    calcium_mg: float | None = None
    iron_mg: float | None = None
    zinc_mg: float | None = None
    cholesterol_mg: float | None = None
    vitamin_a_mcg: float | None = None
    vitamin_c_mg: float | None = None
    vitamin_d_mcg: float | None = None
    vitamin_e_mg: float | None = None
    vitamin_k_mcg: float | None = None
    vitamin_b6_mg: float | None = None
    vitamin_b12_mcg: float | None = None
    folate_mcg: float | None = None
    niacin_mg: float | None = None


@dataclass
class DailyImportData:
    health: DailyHealthData
    nutrition: DailyNutritionData | None = None


@dataclass
class WorkoutData:
    date: datetime.date
    workout_type: str
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    duration_min: float | None = None
    active_energy_kj: float | None = None
    intensity: float | None = None
    max_hr: int | None = None
    avg_hr: int | None = None
    distance_km: float | None = None
    steps: int | None = None


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


def _parse_flexible_datetime(date_str: str) -> datetime.datetime:
    """Parse datetime with or without seconds (e.g. "2026-03-23 09:04" or "2026-03-23 09:04:00")."""
    s = date_str.strip()
    if len(s) >= 19:
        return _parse_datetime(s)
    return datetime.datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def _parse_duration_minutes(value: str) -> float | None:
    """Parse a "H:M:S" or "M:S" duration string into minutes. Returns None if empty/malformed."""
    if not value:
        return None
    parts = value.split(":")
    if len(parts) == 3:
        h, m, s = (float(p) for p in parts)
        return h * 60 + m + s / 60
    if len(parts) == 2:
        m, s = (float(p) for p in parts)
        return m + s / 60
    return None


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
            hr_readings = daily_resting_hr.get(date, [])
            hrv_readings = daily_hrv.get(date, [])
            spo2_readings = daily_spo2.get(date, [])
            results[date] = DailyHealthData(
                date=date,
                steps=daily_steps.get(date) or None,
                active_calories=daily_calories.get(date) or None,
                resting_hr=int(sum(hr_readings) / len(hr_readings)) if hr_readings else None,
                hrv_ms=round(sum(hrv_readings) / len(hrv_readings), 1) if hrv_readings else None,
                spo2_pct=round(sum(spo2_readings) / len(spo2_readings), 1)
                if spo2_readings
                else None,
                sleep_hours=round(daily_sleep_minutes[date] / 60, 1)
                if date in daily_sleep_minutes
                else None,
            )

        return results

    # Column names used by Health Auto Export (Spanish locale)
    CSV_COLUMNS = {
        "date": "Fecha/Hora",
        "sleep_hours": "Análisis del Sueño [Total] (hr)",
        "resting_hr": "Frecuencia Cardiaca en Reposo (bpm)",
        "hrv_ms": "Variabilidad de Frecuencia Cardíaca (ms)",
        "steps": "Conteo de Pasos (pasos)",
        "active_energy_kj": "Energía Activa (kJ)",
        "spo2_pct": "Saturación de Oxígeno en Sangre (%)",
        "sleep_rem_hours": "Análisis del Sueño [REM] (hr)",
        "distance_km": "Distancia de Caminata + Carrera (km)",
        "flights_climbed": "Pisos Subidos (cuenta)",
        "resting_energy_kj": "Energía en Reposo (kJ)",
        "exercise_intensity": "Esfuerzo Físico (kcal/hr·kg)",
        "walking_hr_avg": "Promedio de Frecuencia Cardíaca al Caminar (bpm)",
        "vo2_max": "VO2 Máx (ml/(kg·min))",
        "cardio_recovery": "Recuperación Cardio (cuenta/min)",
        "step_length_cm": "Longitud del Paso al Caminar (cm)",
        "walking_asymmetry_pct": "Porcentaje de Asimetría al Caminar (%)",
        "double_support_pct": "Porcentaje de Doble Apoyo al Caminar (%)",
        "walking_speed_kmh": "Velocidad al Caminar (km/hr)",
        "respiratory_rate": "Frecuencia respiratoria (cuenta/min)",
        "breathing_disturbances": "Alteraciones de la respiración (cuenta)",
        "weight_kg": "Peso (kg)",
        "body_fat_pct": "Porcentaje de grasa corporal (%)",
        "daylight_min": "Tiempo en Luz de Día (min)",
    }

    NUTRITION_COLUMNS = {
        "calories_kj": "Energía Dietética (kJ)",
        "protein_g": "Proteína (g)",
        "carbs_g": "Carbohidratos (g)",
        "fat_total_g": "Grasa Total (g)",
        "fat_saturated_g": "Grasa Saturada (g)",
        "fiber_g": "Fibra (g)",
        "sugar_g": "Azúcar (g)",
        "water_ml": "Agua (mL)",
        "caffeine_mg": "Cafeína (mg)",
        "cholesterol_mg": "Colesterol (mg)",
        "sodium_mg": "Sodio (mg)",
        "potassium_mg": "Potasio (mg)",
        "magnesium_mg": "Magnesio (mg)",
        "calcium_mg": "Calcio (mg)",
        "iron_mg": "Hierro (mg)",
        "zinc_mg": "Zinc (mg)",
        "vitamin_a_mcg": "Vitamina A (mcg)",
        "vitamin_c_mg": "Vitamina C (mg)",
        "vitamin_d_mcg": "Vitamina D (mcg)",
        "vitamin_e_mg": "Vitamina E (mg)",
        "vitamin_k_mcg": "Vitamina K (mcg)",
        "vitamin_b6_mg": "Vitamina B6 (mg)",
        "vitamin_b12_mcg": "Vitamina B12 (mcg)",
        "folate_mcg": "Folato (mcg)",
        "niacin_mg": "Niacina (mg)",
    }

    # Conversion spec: (field_name, converter, decimals)
    # "round" = round to N decimals, "int" = truncate to int
    _HEALTH_FIELD_SPECS: list[tuple[str, str, int]] = [
        ("sleep_hours", "round", 1),
        ("resting_hr", "int", 0),
        ("hrv_ms", "round", 1),
        ("steps", "int", 0),
        ("spo2_pct", "round", 1),
        ("sleep_rem_hours", "round", 1),
        ("distance_km", "round", 2),
        ("flights_climbed", "int", 0),
        ("resting_energy_kj", "round", 1),
        ("exercise_intensity", "round", 2),
        ("walking_hr_avg", "int", 0),
        ("vo2_max", "round", 1),
        ("cardio_recovery", "round", 1),
        ("step_length_cm", "round", 1),
        ("walking_asymmetry_pct", "round", 1),
        ("double_support_pct", "round", 1),
        ("walking_speed_kmh", "round", 2),
        ("respiratory_rate", "round", 1),
        ("breathing_disturbances", "round", 1),
        ("weight_kg", "round", 1),
        ("body_fat_pct", "round", 1),
        ("daylight_min", "round", 1),
    ]

    @staticmethod
    def _csv_float(row: dict[str, str], key: str, columns: dict[str, str]) -> float | None:
        col_name = columns.get(key)
        if col_name is None:
            return None
        val = row.get(col_name, "").strip()
        return float(val) if val else None

    @staticmethod
    def _row_float(row: dict[str, str], col: str) -> float | None:
        val = row.get(col, "").strip()
        return float(val) if val else None

    @staticmethod
    def _row_int(row: dict[str, str], col: str) -> int | None:
        val = row.get(col, "").strip()
        return int(float(val)) if val else None

    @staticmethod
    def _convert_value(raw: float | None, converter: str, decimals: int) -> float | int | None:
        if raw is None:
            return None
        if converter == "int":
            return int(raw)
        return round(raw, decimals)

    def parse_csv(self, csv_path: Path) -> dict[datetime.date, DailyImportData]:
        results: dict[datetime.date, DailyImportData] = {}

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = self.CSV_COLUMNS
            ncols = self.NUTRITION_COLUMNS

            for row in reader:
                date_str = row.get(cols["date"], "")
                if not date_str:
                    continue
                date = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date()

                # --- Health data ---
                health_kwargs: dict = {"date": date}
                for field_name, converter, decimals in self._HEALTH_FIELD_SPECS:
                    raw = self._csv_float(row, field_name, cols)
                    health_kwargs[field_name] = self._convert_value(raw, converter, decimals)

                # active_calories requires kJ-to-kcal conversion
                active_kj = self._csv_float(row, "active_energy_kj", cols)
                health_kwargs["active_calories"] = (
                    int(active_kj / 4.184) if active_kj is not None else None
                )

                health = DailyHealthData(**health_kwargs)

                # --- Nutrition data ---
                nutrition_values: dict[str, float | None] = {}
                has_nutrition = False
                for field_name in ncols:
                    val = self._csv_float(row, field_name, ncols)
                    nutrition_values[field_name] = round(val, 2) if val is not None else None
                    if val is not None:
                        has_nutrition = True

                nutrition: DailyNutritionData | None = None
                if has_nutrition:
                    nutrition = DailyNutritionData(date=date, **nutrition_values)

                results[date] = DailyImportData(health=health, nutrition=nutrition)

        return results

    def parse_workouts_csv(self, csv_path: Path) -> list[WorkoutData]:
        results: list[WorkoutData] = []

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            if "Workout Type" in fieldnames:
                cols = WORKOUT_COLUMNS_V1
            elif "Type" in fieldnames:
                cols = WORKOUT_COLUMNS_V2
            else:
                raise ValueError(
                    f"Unrecognized workout CSV header in {csv_path.name}: "
                    f"expected 'Workout Type' (v1) or 'Type' (v2), got {fieldnames}"
                )

            for row in reader:
                workout_type = row.get(cols["type"], "").strip()
                start_str = row.get("Start", "").strip()
                if not workout_type or not start_str:
                    continue

                start_time = _parse_flexible_datetime(start_str)
                end_str = row.get("End", "").strip()
                end_time = _parse_flexible_datetime(end_str) if end_str else None

                duration_min = _parse_duration_minutes(row.get("Duration", "").strip())
                if duration_min is not None:
                    duration_min = round(duration_min, 1)

                results.append(
                    WorkoutData(
                        date=start_time.date(),
                        workout_type=normalize_workout_type(workout_type),
                        start_time=start_time,
                        end_time=end_time,
                        duration_min=duration_min,
                        active_energy_kj=self._row_float(row, cols["active_energy_kj"]),
                        intensity=self._csv_float(row, "intensity", cols),
                        max_hr=self._row_int(row, cols["max_hr"]),
                        avg_hr=self._row_int(row, cols["avg_hr"]),
                        distance_km=self._row_float(row, cols["distance_km"]),
                        steps=self._row_int(row, cols["steps"]),
                    )
                )

        return results

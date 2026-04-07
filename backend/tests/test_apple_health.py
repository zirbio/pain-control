import datetime
from pathlib import Path

import pytest

from backend.importers.apple_health import (
    AppleHealthImporter,
    DailyHealthData,
    DailyImportData,
    normalize_workout_type,
)

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


def test_parse_csv_extracts_daily_data(tmp_path):
    csv_file = tmp_path / "HealthAutoExport-2026-03-21-2026-03-21.csv"
    csv_file.write_text(
        "Fecha/Hora,Conteo de Pasos (pasos),Energía Activa (kJ),"
        "Frecuencia Cardiaca en Reposo (bpm),"
        "Variabilidad de Frecuencia Cardíaca (ms),"
        "Saturación de Oxígeno en Sangre (%),"
        "Análisis del Sueño [Total] (hr)\n"
        "2026-03-21 00:00:00,7035,1994,54,49.23,98.86,6.4\n"
        "2026-03-22 00:00:00,9543,2828,63,57.01,97.8,6.7\n"
    )
    importer = AppleHealthImporter()
    results = importer.parse_csv(csv_file)

    assert len(results) == 2

    import_data1 = results[datetime.date(2026, 3, 21)]
    assert isinstance(import_data1, DailyImportData)
    day1 = import_data1.health
    assert day1.steps == 7035
    assert day1.active_calories == 476  # 1994 kJ / 4.184
    assert day1.resting_hr == 54
    assert abs(day1.hrv_ms - 49.2) < 0.1
    assert abs(day1.spo2_pct - 98.9) < 0.1
    assert abs(day1.sleep_hours - 6.4) < 0.1

    day2 = results[datetime.date(2026, 3, 22)].health
    assert day2.steps == 9543
    assert day2.resting_hr == 63


def test_parse_csv_handles_empty_values(tmp_path):
    csv_file = tmp_path / "HealthAutoExport-empty.csv"
    csv_file.write_text(
        "Fecha/Hora,Conteo de Pasos (pasos),Energía Activa (kJ),"
        "Frecuencia Cardiaca en Reposo (bpm),"
        "Variabilidad de Frecuencia Cardíaca (ms),"
        "Saturación de Oxígeno en Sangre (%),"
        "Análisis del Sueño [Total] (hr)\n"
        "2026-03-21 00:00:00,,,,,, \n"
    )
    importer = AppleHealthImporter()
    results = importer.parse_csv(csv_file)

    day = results[datetime.date(2026, 3, 21)].health
    assert day.steps is None
    assert day.resting_hr is None
    assert day.sleep_hours is None


def test_parse_csv_extracts_extended_health_and_nutrition(tmp_path):
    csv_file = tmp_path / "HealthAutoExport-full.csv"
    csv_file.write_text(
        "Fecha/Hora,Conteo de Pasos (pasos),Energía Activa (kJ),"
        "Frecuencia Cardiaca en Reposo (bpm),"
        "Variabilidad de Frecuencia Cardíaca (ms),"
        "Saturación de Oxígeno en Sangre (%),"
        "Análisis del Sueño [Total] (hr),"
        "Análisis del Sueño [REM] (hr),"
        "Distancia de Caminata + Carrera (km),"
        "Porcentaje de Asimetría al Caminar (%),"
        "Velocidad al Caminar (km/hr),"
        "VO2 Máx (ml/(kg·min)),"
        "Proteína (g),"
        "Carbohidratos (g),"
        "Cafeína (mg),"
        "Vitamina D (mcg)\n"
        "2026-03-21 00:00:00,7035,1994,54,49.23,98.86,6.4,"
        "1.79,5.23,27.11,3.47,42.5,"
        "148.76,198.05,1184,1.77\n"
    )
    importer = AppleHealthImporter()
    results = importer.parse_csv(csv_file)

    data = results[datetime.date(2026, 3, 21)]
    h = data.health
    assert abs(h.sleep_rem_hours - 1.8) < 0.1
    assert abs(h.distance_km - 5.23) < 0.01
    assert abs(h.walking_asymmetry_pct - 27.1) < 0.1
    assert abs(h.walking_speed_kmh - 3.47) < 0.1
    assert abs(h.vo2_max - 42.5) < 0.1

    n = data.nutrition
    assert n is not None
    assert abs(n.protein_g - 148.76) < 0.01
    assert abs(n.carbs_g - 198.05) < 0.01
    assert abs(n.caffeine_mg - 1184) < 0.1
    assert abs(n.vitamin_d_mcg - 1.77) < 0.01


def test_parse_workouts_csv(tmp_path):
    csv_file = tmp_path / "Workouts-test.csv"
    csv_file.write_text(
        "Workout Type,Start,End,Duration,"
        "Energía Activa (kJ),Energía en Reposo (kJ),"
        "Intensidad (kcal/hr·kg),"
        "Frecuencia Cardíaca Máxima (bpm),"
        "Frecuencia Cardíaca Promedio (bpm),"
        "Distancia (km),"
        "Velocidad Máx. (km/hr),Veloc. Prom. (km/hr),"
        "Pisos Subidos,Elevación Ascendida (m),"
        "Elevación Descendida (m),Conteo de Pasos,"
        "Cadencia de Paso (spm)\n"
        "Pilates,2026-03-23 09:04,2026-03-23 10:03,00:58:41,"
        "1201.17,396.73,5.24,141,110,0.0,0.0,0.0,0,0,0,116,1.97\n"
        "Interior Ciclismo,2026-03-22 09:19,2026-03-22 09:59,00:40:02,"
        "953.95,201.81,0.0,158,134,9.70,0.0,0.0,0,0,0,12,0.30\n"
    )
    importer = AppleHealthImporter()
    workouts = importer.parse_workouts_csv(csv_file)

    assert len(workouts) == 2

    pilates = workouts[0]
    assert pilates.workout_type == "Pilates"
    assert pilates.date == datetime.date(2026, 3, 23)
    assert abs(pilates.duration_min - 58.7) < 0.1
    assert pilates.max_hr == 141
    assert pilates.avg_hr == 110
    assert abs(pilates.active_energy_kj - 1201.17) < 0.01

    ciclismo = workouts[1]
    assert ciclismo.workout_type == "Indoor Cycling"
    assert ciclismo.date == datetime.date(2026, 3, 22)
    assert abs(ciclismo.distance_km - 9.70) < 0.01
    assert ciclismo.max_hr == 158


def test_parse_csv_with_real_data():
    """Integration test with real exported data."""
    csv_path = (
        Path(__file__).parent.parent.parent
        / "data"
        / "imports"
        / "HealthAutoExport-2026-03-21-2026-03-28.csv"
    )
    if not csv_path.exists():
        pytest.skip("real data file not available")

    importer = AppleHealthImporter()
    results = importer.parse_csv(csv_path)
    assert len(results) == 8

    day = results[datetime.date(2026, 3, 26)]
    h = day.health
    assert h.steps == 11357
    assert h.walking_asymmetry_pct is not None
    assert h.vo2_max is not None

    n = day.nutrition
    assert n is not None
    assert n.protein_g is not None
    assert n.protein_g > 0


def test_parse_workouts_csv_duration_two_parts(tmp_path):
    """Gap A: Duration in MM:SS format (2 parts)."""
    csv_file = tmp_path / "Workouts-mmss.csv"
    csv_file.write_text(
        "Workout Type,Start,End,Duration,Energía Activa (kJ)\n"
        "Walking,2026-03-21 08:00,2026-03-21 08:45,45:00,500\n"
        "Running,2026-03-21 10:00,2026-03-21 10:30,,600\n"
    )
    importer = AppleHealthImporter()
    workouts = importer.parse_workouts_csv(csv_file)
    assert len(workouts) == 2
    assert abs(workouts[0].duration_min - 45.0) < 0.1
    assert workouts[1].duration_min is None


def test_parse_workouts_csv_empty_file(tmp_path):
    """Gap G: Workouts CSV with headers only."""
    csv_file = tmp_path / "Workouts-empty.csv"
    csv_file.write_text("Workout Type,Start,End,Duration,Energía Activa (kJ)\n")
    importer = AppleHealthImporter()
    workouts = importer.parse_workouts_csv(csv_file)
    assert workouts == []


def test_parse_csv_no_nutrition_columns(tmp_path):
    """Gap F: CSV with only health columns, no nutrition headers."""
    csv_file = tmp_path / "HealthAutoExport-health-only.csv"
    csv_file.write_text(
        "Fecha/Hora,Conteo de Pasos (pasos),Energía Activa (kJ)\n2026-03-21 00:00:00,5000,1000\n"
    )
    importer = AppleHealthImporter()
    results = importer.parse_csv(csv_file)
    data = results[datetime.date(2026, 3, 21)]
    assert data.health.steps == 5000
    assert data.nutrition is None


def test_normalize_workout_type_known_types():
    assert normalize_workout_type("Entrenamiento de Fuerza Funcional") == "Rehabilitation"
    assert normalize_workout_type("Interior Ciclismo") == "Indoor Cycling"
    assert normalize_workout_type("Pilates") == "Pilates"
    assert normalize_workout_type("Caminata") == "Walking"
    assert normalize_workout_type("Yoga") == "Yoga"
    assert normalize_workout_type("Natación") == "Swimming"
    assert normalize_workout_type("Ciclismo") == "Cycling"
    assert normalize_workout_type("Elíptica") == "Elliptical"
    assert normalize_workout_type("Estiramientos") == "Stretching"
    assert normalize_workout_type("Golf") == "Golf"


def test_normalize_workout_type_unknown_passthrough(caplog):
    result = normalize_workout_type("Escalada en Roca")
    assert result == "Escalada en Roca"
    assert "Unknown workout type" in caplog.text


def test_parse_workouts_csv_v2_english_format(tmp_path):
    """v2 format: Health Auto Export switched to English headers (~Mar 2026)."""
    csv_file = tmp_path / "Workouts-2026-04-06.csv"
    csv_file.write_text(
        "Type,Start,End,Duration,Total Energy (kJ),Active Energy (kJ),"
        "Max Heart Rate (bpm),Avg Heart Rate (bpm),Distance (km),"
        "Avg Speed (km/hr),Step Count (count),Step Cadence (spm),"
        "Swimming Stroke Count (count),Swim Stoke Cadence (spm),"
        "Flights Climbed (count),Elevation Ascended (m),Elevation Descended (m)\n"
        "Golf,2026-04-06 16:32,2026-04-06 18:35,02:02:45,4343,3436,"
        "141,105.78,3.59,1.76,5068,41.29,,,,,\n"
        "Pilates,2026-04-06 09:03,2026-04-06 10:02,00:58:41,1315,918.18,"
        "127,93.75,,,100,1.7,,,,,\n"
    )
    importer = AppleHealthImporter()
    workouts = importer.parse_workouts_csv(csv_file)

    assert len(workouts) == 2

    golf = workouts[0]
    assert golf.workout_type == "Golf"
    assert golf.date == datetime.date(2026, 4, 6)
    assert abs(golf.duration_min - 122.75) < 0.1
    assert golf.max_hr == 141
    assert golf.avg_hr == 105
    assert abs(golf.active_energy_kj - 3436) < 0.01
    assert abs(golf.distance_km - 3.59) < 0.01
    assert golf.steps == 5068
    # v2 has no intensity column
    assert golf.intensity is None

    pilates = workouts[1]
    assert pilates.workout_type == "Pilates"
    assert pilates.date == datetime.date(2026, 4, 6)
    assert pilates.max_hr == 127
    assert pilates.avg_hr == 93
    assert abs(pilates.active_energy_kj - 918.18) < 0.01
    # Distance column present but empty for indoor Pilates
    assert pilates.distance_km is None
    assert pilates.steps == 100
    assert pilates.intensity is None


def test_parse_workouts_csv_unknown_header_raises(tmp_path):
    """Unknown header schema must raise loudly, not silently return []."""
    csv_file = tmp_path / "Workouts-future.csv"
    csv_file.write_text(
        "Activity,Started,Ended,Length\nYoga,2026-05-01 08:00,2026-05-01 08:45,45:00\n"
    )
    importer = AppleHealthImporter()
    with pytest.raises(ValueError, match="Unrecognized workout CSV header"):
        importer.parse_workouts_csv(csv_file)


def test_parse_workouts_csv_v2_unknown_workout_type_passthrough(tmp_path, caplog):
    """v2 with an unmapped Type value passes through and logs a warning."""
    csv_file = tmp_path / "Workouts-2026-04-07.csv"
    csv_file.write_text(
        "Type,Start,End,Duration,Active Energy (kJ),"
        "Max Heart Rate (bpm),Avg Heart Rate (bpm),"
        "Distance (km),Step Count (count)\n"
        "Pickleball,2026-04-07 18:00,2026-04-07 19:00,01:00:00,800,145,120,,500\n"
    )
    importer = AppleHealthImporter()
    with caplog.at_level("WARNING"):
        workouts = importer.parse_workouts_csv(csv_file)
    assert len(workouts) == 1
    assert workouts[0].workout_type == "Pickleball"
    assert "Unknown workout type" in caplog.text


def test_parse_workouts_csv_v2_empty_file(tmp_path):
    """v2 with only the header row returns []."""
    csv_file = tmp_path / "Workouts-empty-v2.csv"
    csv_file.write_text(
        "Type,Start,End,Duration,Active Energy (kJ),"
        "Max Heart Rate (bpm),Avg Heart Rate (bpm),"
        "Distance (km),Step Count (count)\n"
    )
    importer = AppleHealthImporter()
    assert importer.parse_workouts_csv(csv_file) == []


def test_parse_workouts_csv_v2_skips_rows_missing_required_fields(tmp_path):
    """v2 rows without Type or Start are silently skipped (not crashed)."""
    csv_file = tmp_path / "Workouts-partial-v2.csv"
    csv_file.write_text(
        "Type,Start,End,Duration,Active Energy (kJ),"
        "Max Heart Rate (bpm),Avg Heart Rate (bpm),"
        "Distance (km),Step Count (count)\n"
        ",2026-04-06 09:00,2026-04-06 10:00,01:00:00,500,140,110,,100\n"
        "Yoga,,,,,,,,\n"
        "Pilates,2026-04-06 11:00,2026-04-06 12:00,01:00:00,400,130,100,,80\n"
    )
    importer = AppleHealthImporter()
    workouts = importer.parse_workouts_csv(csv_file)
    assert len(workouts) == 1
    assert workouts[0].workout_type == "Pilates"


def test_parse_workouts_csv_v2_missing_end_time(tmp_path):
    """v2 row with Start but no End still parses, end_time stays None."""
    csv_file = tmp_path / "Workouts-no-end-v2.csv"
    csv_file.write_text(
        "Type,Start,End,Duration,Active Energy (kJ),"
        "Max Heart Rate (bpm),Avg Heart Rate (bpm),"
        "Distance (km),Step Count (count)\n"
        "Caminata,2026-04-06 08:00,,30:00,200,120,90,2.0,2500\n"
    )
    importer = AppleHealthImporter()
    workouts = importer.parse_workouts_csv(csv_file)
    assert len(workouts) == 1
    assert workouts[0].end_time is None
    assert workouts[0].duration_min is not None
    assert abs(workouts[0].duration_min - 30.0) < 0.1


def test_parse_workouts_csv_v2_duration_two_parts(tmp_path):
    """v2 duration in MM:SS format parses correctly (shared parser with v1)."""
    csv_file = tmp_path / "Workouts-mmss-v2.csv"
    csv_file.write_text(
        "Type,Start,End,Duration,Active Energy (kJ),"
        "Max Heart Rate (bpm),Avg Heart Rate (bpm),"
        "Distance (km),Step Count (count)\n"
        "Estiramientos,2026-04-06 07:00,2026-04-06 07:15,15:00,80,95,75,,0\n"
    )
    importer = AppleHealthImporter()
    w = importer.parse_workouts_csv(csv_file)[0]
    assert abs(w.duration_min - 15.0) < 0.1

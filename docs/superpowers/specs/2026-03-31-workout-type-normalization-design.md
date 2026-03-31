# Workout Type Normalization

**Date:** 2026-03-31
**Status:** Approved

## Problem

Workout types imported from Apple Health via Health Auto Export arrive in Spanish (iPhone locale). This creates inconsistent, locale-dependent data that would break if the phone language changes and is harder to analyze programmatically.

Current values in DB: "Interior Ciclismo", "Pilates", "Entrenamiento de Fuerza Funcional".

## Decision

Normalize workout types to canonical English names at import time, with a one-shot migration for existing records.

## Mapping Dictionary

| CSV (Spanish)                       | Normalized (English) |
|-------------------------------------|----------------------|
| Entrenamiento de Fuerza Funcional   | Rehabilitation       |
| Pilates                             | Pilates              |
| Interior Ciclismo                   | Indoor Cycling       |
| Caminata                            | Walking              |
| Yoga                                | Yoga                 |
| Natación                            | Swimming             |
| Ciclismo                            | Cycling              |
| Elíptica                            | Elliptical           |
| Estiramientos                       | Stretching           |
| Golf                                | Golf                 |

"Rehabilitation" is intentional — in this project's context (chronic pain management), functional strength training is rehabilitation work, not general fitness.

## Fallback Behavior

Unknown workout types (not in the map) are stored as-is with a `logger.warning`. This allows incremental expansion of the map without data loss.

## Changes

### 1. Importador — `backend/backend/importers/apple_health.py`

- Add `WORKOUT_TYPE_MAP` constant dictionary at module level.
- Add `normalize_workout_type(raw_type: str) -> str` function that looks up the map and falls back to the raw value with a warning.
- Apply normalization in `parse_workouts_csv()` when constructing `WorkoutData`.

### 2. Migration — Alembic

- New Alembic migration that updates the 3 existing `workout_records` rows using the same mapping via a `CASE` statement.

### No Changes Required

- **Model** (`WorkoutRecord`): `workout_type` stays as `String(100)` — no schema change.
- **Pydantic schemas**: `WorkoutRecordResponse` unchanged.
- **Frontend**: Already displays `workout_type` directly — normalized English names will display automatically.
- **Analysis engine**: Does not reference `workout_type` (only aggregates like `workout_count`, `workout_total_min`).

## Testing

- Unit test for `normalize_workout_type`: known types map correctly, unknown types pass through with warning.
- Update existing `parse_workouts_csv` tests to assert normalized output.
- Migration test: verify idempotency (running twice produces same result).

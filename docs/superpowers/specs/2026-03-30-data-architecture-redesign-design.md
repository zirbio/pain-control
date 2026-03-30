# Data Architecture Redesign

**Date:** 2026-03-30
**Status:** Approved
**Goal:** Clean up the data model to eliminate redundancy, promote subjective fields to DailyEntry, derive objective metrics from Apple Health, and enable per-location pain analysis.

## Motivation

The current architecture has accumulated organic complexity:
- Tables that are always 1:1 modeled as 1:N (Mood, Stress)
- Redundant manual vs auto-imported data (NutritionRecord vs NutritionImportRecord, ActivityRecord vs WorkoutRecord)
- Analysis engine flattens multi-location pain into `pain_max`/`pain_mean`, losing per-location correlation capability
- Stress is collected subjectively when HRV provides an objective proxy
- NutritionRecord exists for 5 fields but only `alcohol` is used manually

## Design

### DailyEntry (expanded)

The main table absorbs fields from eliminated child tables and gains new habit/supplement tracking.

```
-- Identity
date                    DATE, unique, NOT NULL
created_at              DATETIME, auto
updated_at              DATETIME, auto

-- Mood (promoted from MoodRecord)
mood_score              INT 1-10, NOT NULL
mood_emotions           TEXT (JSON list), nullable

-- Stress (optional subjective annotation)
stress_source           TEXT, nullable

-- Activity impact (promoted from ActivityRecord)
activity_pain_effect    TEXT, nullable  ("mejoró" / "empeoró" / "sin cambio")

-- Daily habits (boolean block)
stretching              BOOL, NOT NULL
alcohol                 BOOL, NOT NULL
heavy_dinner            BOOL, NOT NULL

-- Supplements
omega3                  BOOL, NOT NULL
vitamin_d               BOOL, NOT NULL
magnesium               BOOL, NOT NULL
turmeric                BOOL, NOT NULL
```

### Child tables retained (1:N real)

**PainRecord** — unchanged
```
location        TEXT, NOT NULL
intensity       INT 0-10, NOT NULL
pattern         TEXT, nullable
time_of_day     TEXT, nullable
notes           TEXT, nullable
```

**MedicationRecord** — unchanged
```
name            TEXT, NOT NULL
dose            TEXT, nullable
time_taken      TEXT, nullable
effectiveness   INT 0-10, nullable
```

### Auto-imported tables (unchanged)

- **AppleHealthRecord** — sleep, HR, HRV, steps, gait, body composition, respiratory (24 fields)
- **NutritionImportRecord** — macros, vitamins, minerals from MacroFactor (18 fields)
- **WorkoutRecord** — type, duration, HR, distance, energy
- **WeatherRecord** — temperature, humidity, pressure, conditions

### Extras table (unchanged)

Arbitrary key-value pairs for schema evolution. Still not used in analysis — promotion path remains manual via Alembic migration.

### Tables eliminated

| Table | Reason | Where data goes |
|-------|--------|-----------------|
| `MoodRecord` | Always 1:1 with DailyEntry | `mood_score`, `mood_emotions` on DailyEntry |
| `StressRecord` | Level derived from HRV; source is optional annotation | `stress_source` on DailyEntry, `stress_proxy` computed in analysis |
| `ActivityRecord` | Redundant with WorkoutRecord (auto-imported) | `activity_pain_effect` on DailyEntry, workouts from Apple Health |
| `NutritionRecord` | Only `alcohol` used manually; rest from MacroFactor | `alcohol` on DailyEntry, `heavy_dinner` new field |

## Analysis Engine Changes

### Per-location pain correlation

Instead of only `pain_max` and `pain_mean`, `build_daily_dataframe()` will produce:

```
pain_max                — global max (kept for backwards compat)
pain_mean               — global mean (kept)
pain_lumbar_intensity   — max intensity for location "lumbar"
pain_tobillo_intensity  — max intensity for location containing "tobillo"
pain_ciatica_intensity  — max intensity for location containing "ciática"
pain_{location}_intensity — dynamic, based on locations seen in data
```

This enables questions like "does humidity correlate with lumbar pain specifically?" and "does stretching help ankle pain more than lumbar?"

### Stress proxy from HRV

New computed variable in analysis (not stored in DB):

```python
stress_proxy = normalize_against_baseline(hrv_ms)
# Lower HRV relative to personal baseline → higher stress proxy
# Uses rolling 30-day window for baseline
# Output: 0-10 scale (inverted: low HRV = high stress)
```

### New variables from DailyEntry fields

```
mood_score              — direct from DailyEntry
alcohol                 — bool → int
heavy_dinner            — bool → int
stretching              — bool → int
omega3                  — bool → int
vitamin_d               — bool → int
magnesium               — bool → int
turmeric                — bool → int
activity_pain_effect    — categorical encoding
```

## Migration Strategy

### Data migration

1. Migrate existing `MoodRecord` data → `mood_score`/`mood_emotions` on parent DailyEntry
2. Migrate existing `StressRecord.source` → `stress_source` on DailyEntry (level is dropped — will be derived)
3. Migrate existing `ActivityRecord.pain_effect` → `activity_pain_effect` on DailyEntry
4. Migrate existing `NutritionRecord.alcohol` → `alcohol` on DailyEntry
5. New boolean fields (`heavy_dinner`, `omega3`, `vitamin_d`, `magnesium`, `turmeric`) default to `false` for historical entries
6. Drop eliminated tables after data migration is verified

### Backwards compatibility

- API response schema (`DailyEntryResponse`) changes — eliminated record lists removed, new fields added
- Frontend components that read `mood_records[0].score` must switch to `mood_score`
- Check-in skill updated to match new field structure
- Analysis engine updated to use new field locations

## Check-in Flow (post-redesign)

```
Automatic (no questions):
  Apple Health  → sleep, HR, HRV, steps, workouts, nutrition, gait, body comp
  MacroFactor   → macros, vitamins, minerals, caffeine, water
  Open-Meteo    → weather
  Derived       → stress_proxy (from HRV)

Manual — 5 blocks:
  1. Pain       → where, intensity, pattern, timing (multiple locations)
  2. Medication → what, dose, when, effectiveness (multiple meds)
  3. Mood       → score 1-10, emotions
  4. Habits     → stretching? alcohol? heavy dinner? omega3? vit D? magnesium? turmeric?
  5. Activity   → did it affect pain? (optional, only if relevant)

Optional:
  - Stress source annotation (free text)
  - Subjective sleep quality (only if mentioned)
  - Extras (arbitrary key-value)
```

## Out of Scope

- Supabase migration (evaluated and discarded — no benefit for local personal app)
- Extras auto-promotion system (remains manual)
- Mobile app / multi-device sync
- Sharing data with healthcare providers

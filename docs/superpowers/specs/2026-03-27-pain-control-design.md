# Pain Control — Design Spec

Personal chronic pain tracking system that collects daily data through natural language via Claude skills, imports health metrics from Apple Watch, captures weather data automatically, and analyzes correlations to discover pain patterns.

## Context

- Post-accident (18/01/2023) chronic sacro-lumbar pain with L2-L4 fixation
- Persistent left ankle pain
- Daily tramadol + paracetamol (Captor) since early 2025
- Sensitivity to barometric pressure changes, sleep quality, and activity levels
- Goal: find actionable patterns to better manage pain

## Architecture: Python Backend + React Dashboard

```
pain-control/
├── backend/
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   ├── routers/
│   │   │   ├── entries.py           # CRUD daily entries
│   │   │   ├── analysis.py          # Correlation endpoints
│   │   │   └── imports.py           # Trigger Apple Health import
│   │   └── schemas.py               # Pydantic models
│   ├── db/
│   │   ├── database.py              # SQLite connection + engine
│   │   ├── models.py                # SQLAlchemy models
│   │   └── migrations/              # Alembic (schema evolution)
│   ├── importers/
│   │   ├── apple_health.py          # XML → daily records
│   │   ├── weather.py               # OpenWeatherMap API
│   │   └── watcher.py               # Directory monitor for auto-imports (phase C)
│   ├── analysis/
│   │   ├── correlations.py          # Pandas: variable correlations
│   │   ├── trends.py                # Temporal evolution, moving averages
│   │   ├── patterns.py              # Pattern detection (flare clusters)
│   │   └── reports.py               # Weekly/monthly report generation
│   └── core/
│       ├── config.py                # Settings (API keys, paths)
│       └── schema_manager.py        # Extras → formal field promotion
├── dashboard/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PainTimeline.tsx      # Interactive pain timeline
│   │   │   ├── CorrelationMatrix.tsx # Correlation heatmap
│   │   │   ├── TrendChart.tsx        # Multi-variable trend lines
│   │   │   ├── DailyDetail.tsx       # Single day detail view
│   │   │   ├── WeatherOverlay.tsx    # Barometric pressure vs pain
│   │   │   ├── LagExplorer.tsx       # Lag correlation explorer
│   │   │   └── PeriodComparison.tsx  # Side-by-side period comparison
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx         # Main overview
│   │   │   ├── Analysis.tsx          # Correlation exploration
│   │   │   └── History.tsx           # Navigable history
│   │   └── hooks/
│   │       └── useApi.ts             # FastAPI client
│   └── package.json
├── skills/                           # Claude Code skills
│   ├── pain-checkin.md
│   ├── pain-analyze.md
│   ├── pain-report.md
│   ├── pain-import.md
│   └── pain-schema.md
├── data/
│   ├── pain-control.db               # SQLite database
│   └── imports/                       # Apple Health XML drop directory
└── docs/
```

## Data Model (SQLite)

### daily_entries
One row per day. Central reference for all other tables.

| Field | Type | Source |
|---|---|---|
| id | INTEGER PK | auto |
| date | DATE UNIQUE | auto |
| created_at | TIMESTAMP | auto |
| updated_at | TIMESTAMP | auto |

### pain_records
Multiple per day (lumbar + ankle + sciatica can coexist).

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK → daily_entries | |
| location | TEXT | "lumbar", "tobillo_izquierdo", "ciática" |
| intensity | INTEGER 0-10 | 6 |
| pattern | TEXT | "constante", "intermitente", "matutino" |
| time_of_day | TEXT | "mañana", "tarde", "noche" |
| notes | TEXT | "empeoró después de estar sentado 2h" |

### medication_records

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| name | TEXT | "Captor" |
| dose | TEXT | "75mg tramadol + paracetamol" |
| time_taken | TIME | 08:00 |
| effectiveness | INTEGER 0-10 | 7 |

### mood_records

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| score | INTEGER 1-10 | 6 |
| emotions | JSON | ["frustración", "cansancio"] |
| notes | TEXT | |

### activity_records

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| type | TEXT | "caminata", "bici_kickr", "CARs", "fisio" |
| duration_min | INTEGER | 30 |
| pain_effect | TEXT | "mejoró", "empeoró", "sin_cambio" |
| notes | TEXT | |

### stress_records

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| level | INTEGER 1-10 | 7 |
| source | TEXT | "laboral", "personal", "físico" |
| notes | TEXT | |

### nutrition_records

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| meals | JSON | [{"meal": "almuerzo", "description": "..."}] |
| alcohol | BOOLEAN | false |
| caffeine_cups | INTEGER | 2 |
| water_liters | REAL | 1.5 |
| notes | TEXT | |

### weather_records
Populated automatically via OpenWeatherMap API on each check-in.

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| temperature_c | REAL | 14.5 |
| humidity_pct | REAL | 78 |
| pressure_hpa | REAL | 1008.3 |
| pressure_change_hpa | REAL | -5.2 |
| conditions | TEXT | "lluvia" |
| location | TEXT | "Madrid" |

### apple_health_records
Populated via Apple Health XML import.

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| sleep_hours | REAL | 6.5 |
| sleep_quality | TEXT | cycle data |
| resting_hr | INTEGER | 62 |
| hrv_ms | REAL | 38.5 |
| steps | INTEGER | 8432 |
| active_calories | INTEGER | 340 |
| spo2_pct | REAL | 97 |
| raw_data | JSON | full day dump |

### extras
Flexible key-value store for evolving fields.

| Field | Type | Example |
|---|---|---|
| id | INTEGER PK | auto |
| entry_id | FK | |
| key | TEXT | "rigidez_matutina" |
| value | TEXT | "7" |
| value_type | TEXT | "integer", "text", "boolean" |
| first_seen | DATE | when this key first appeared |

### schema_fields
Tracks fields promoted from extras to formal columns.

| Field | Type | Purpose |
|---|---|---|
| id | INTEGER PK | auto |
| field_name | TEXT | "rigidez_matutina" |
| promoted_date | DATE | when it became formal |
| table_name | TEXT | which table it lives in |
| description | TEXT | what it measures |

## Schema Evolution

1. New field mentioned in check-in → saved to `extras` as key-value
2. If a key appears >5 times → Claude suggests promoting to formal field
3. On user approval → Alembic migration: new column, historical data migrated from extras, check-in prompt updated

## Data Flow

Three data sources feed the system:

### Manual (voice via Claude skill)
- Pain intensity/location/pattern, medication, mood, stress, activity, nutrition, notes, extras
- Claude parses free text, extracts structured fields, asks for missing required fields

### Automatic — Apple Health (import)
- Sleep (hours, quality, cycles), resting HR, HRV, steps, active calories, SpO2
- Phase B: iOS Shortcut exports XML → AirDrop/iCloud → `data/imports/`
- Phase C: Health Export CSV app auto-syncs to monitored directory

### Automatic — Weather API
- Temperature, humidity, barometric pressure (+ daily change), conditions
- Triggered automatically with each check-in
- User's default location configured in `config.py` (no auto-detection needed for a single-user daily check-in)
- `pressure_change_hpa` is computed: today's pressure minus yesterday's stored value
- OpenWeatherMap free tier (1000 calls/day), requires free API key

## Analysis Engine

### Correlation types

**Simple (pair-wise):** Pearson/Spearman between any two variables. Configurable time windows (7d, 30d, 90d, all).

**Lag correlations (temporal offset):** Cross-correlation with lags -3 to +3 days. Critical for: sleep→next-day pain, exercise→next-day pain, pressure drop→pain 24-48h later, missed medication→pain onset delay.

**Pattern detection:** K-means clustering on daily feature vectors to identify "bad day profiles" (e.g., poor sleep + high humidity + high stress = flare). Periodicity detection for weekly/seasonal cycles.

**Long-term trends:** 7-day and 30-day moving averages, linear regression for trend direction, statistical tests for period comparison (pre/post medication change, pre/post physio).

### Alert system

Proactive detection surfaced in reports and check-ins:

| Alert type | Example |
|---|---|
| Strong new correlation | "Days with >8000 steps: -2.1 pain points next day (p<0.05)" |
| Trend change | "Average pain rose from 4.2 to 5.8 over last 2 weeks" |
| Flare pattern | "Last 3 flares (>7/10) coincided with >8 hPa pressure drops" |
| Medication effectiveness | "Captor effectiveness trending down: 7.2 → 5.1 over 60 days" |
| Recurring extra field | "'rigidez_matutina' reported 6 times — promote to formal?" |

### Natural language queries (`/pain-analyze`)

Claude translates questions into analysis operations:

- "Do rainy days hurt more?" → filter + compare means + significance test
- "What helps the most?" → rank negative correlations with pain (top 5)
- "Compare February vs March" → side-by-side period statistics
- "When was my last bad flare and what happened?" → find last day ≥8, show full context

### Reports (`/pain-report`)

Weekly/monthly structured reports:

- Pain summary (mean, range, good/bad day count, trend)
- Sleep impact analysis
- Activity impact analysis
- Weather correlation highlights
- Medication effectiveness tracking
- Top correlations for the period
- Active alerts

## Claude Skills

### /pain-checkin (daily check-in)

1. Receive free-form text describing the day
2. Extract structured fields (pain, sleep, medication, activity, mood, stress, nutrition, extras)
3. Identify missing required fields and ask follow-up questions
4. Call OpenWeatherMap API for weather data
5. POST structured entry to FastAPI
6. Check for relevant alerts and surface them
7. If new fields detected, store in extras

Required fields (Claude asks if missing): pain (at least one location + intensity), medication, mood score.

Optional fields (captured if mentioned, not prompted): activity, stress, nutrition, extras.

### /pain-analyze (ad-hoc queries)

1. Receive natural language question
2. Determine analysis type (correlation, comparison, trend, lookup)
3. Call appropriate analysis endpoint
4. Present results in natural language with statistical context

### /pain-report (periodic reports)

1. Accept period: "semana", "mes", or custom date range
2. Call report generation endpoint
3. Present formatted report with all sections

### /pain-import (Apple Health import)

1. Scan `data/imports/` for new XML files
2. Parse using apple-health-parser library
3. Extract daily aggregates: sleep, HR, HRV, steps, calories, SpO2
4. Merge with existing records (no duplicates)
5. Report import summary

### /pain-schema (schema management)

1. Show current active fields across all tables
2. Show extras in use with occurrence count
3. Suggest promotions for frequent extras
4. On approval: run Alembic migration, migrate data, update check-in prompt

## Dashboard (Next.js + React)

### Pages

**Dashboard (main overview)**
- Pain Timeline: multi-series line chart (lumbar=red, ankle=orange, sciatica=yellow)
- Summary cards: 7-day pain average, trend arrow, sleep average, active days, medication effectiveness
- Weekly heatmap: GitHub-contributions style, color = pain intensity
- Active alerts panel

**Analysis (exploration)**
- Correlation Matrix: interactive heatmap, click cell → scatter plot detail
- Lag Explorer: two-variable selector + lag slider (-3 to +3 days)
- Period Comparison: select two date ranges, side-by-side statistics
- Weather Overlay: dual-axis chart, pain + barometric pressure

**History (browsable log)**
- Calendar view: click any day for full entry detail
- Filters: pain range, location, factor presence
- Export: CSV/JSON from any filtered view

### Tech stack

| Piece | Choice | Rationale |
|---|---|---|
| Framework | Next.js | Routing, fast loading, mature ecosystem |
| Charts | Recharts + Nivo | Recharts for lines/bars, Nivo for heatmaps/correlations |
| UI | Tailwind + shadcn/ui | Fast, clean, accessible components |
| State | TanStack Query | FastAPI cache, auto-refetch |
| Dates | date-fns | Lightweight date manipulation |

Desktop-first, responsive for iPhone consultation.

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy, Alembic, Pandas, SciPy |
| Database | SQLite (local file) |
| Importers | apple-health-parser (pip), OpenWeatherMap API |
| Dashboard | Next.js, TypeScript, Recharts, Nivo, Tailwind, shadcn/ui |
| Skills | Claude Code skills (markdown) |
| Data format | JSON over REST (FastAPI ↔ Dashboard, Skills ↔ FastAPI) |

## Apple Health Import Phases

**Phase B (initial):** iOS Shortcut exports Health data as XML → transfer to Mac via AirDrop or iCloud → drop in `data/imports/` → run `/pain-import`.

**Phase C (future):** Health Export CSV app auto-syncs to a directory → `watcher.py` monitors for new files → auto-import on detection.

The system accepts any file dropped in `data/imports/` regardless of how it got there — the source is interchangeable.

## Not in scope (for now)

- Mobile app (iPhone) — use dashboard responsive + Claude terminal
- Multi-user support — single user, local only
- Cloud sync / backup — local SQLite, user manages backups
- Medical advice — the system finds correlations, does not prescribe
- Real-time notifications — alerts surface in reports and check-ins only

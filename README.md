# Pain Control

[![Backend CI](https://github.com/zirbio/pain-control/actions/workflows/backend.yml/badge.svg)](https://github.com/zirbio/pain-control/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/zirbio/pain-control/actions/workflows/frontend.yml/badge.svg)](https://github.com/zirbio/pain-control/actions/workflows/frontend.yml)

Personal chronic pain tracking and analysis system. Collects daily pain entries, medication, mood, activity, and health data to find patterns and correlations over time.

## Architecture

- **Backend**: Python 3.12 · FastAPI · SQLAlchemy · SQLite · Alembic
- **Frontend**: Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 · shadcn/ui
- **Analysis**: Pandas · SciPy · correlation matrix · lag analysis · trend detection
- **Integrations**: Apple Health import · Open-Meteo weather API

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn backend.api.main:app --reload --port 8420
```

API available at `http://localhost:8420` — interactive docs at `/docs`.

### Frontend

```bash
cd dashboard
npm install
npm run dev
```

Dashboard available at `http://localhost:3000`.

## Usage

### Daily workflow

1. **Import health data** — Export Apple Health XML to `data/imports/` and run the import
2. **Record your day** — Describe how you felt in natural language; the system extracts structured data
3. **Check patterns** — Ask questions about correlations, trends, and triggers
4. **Review the dashboard** — Visual metrics, pain timeline, and weekly heatmaps at `localhost:3000`

### Claude Code skills

If you use [Claude Code](https://claude.ai/claude-code), the project includes skills that let you interact conversationally:

| Skill | What it does |
|---|---|
| `/pain-checkin` | Daily check-in. Write freely (e.g. *"ayer lumbar 5, ibuprofeno a las 8, ánimo 6, caminé media hora"*) and it parses, asks for missing fields, fetches weather, and saves via the API |
| `/pain-report semana` | Weekly report with pain averages, sleep, activity, top correlations, and alerts |
| `/pain-report mes` | Monthly report |
| `/pain-report 2026-01-01 2026-03-31` | Custom date range report |
| `/pain-analyze` | Free-form questions: *"¿el sueño afecta mi dolor?"*, *"¿cuándo fue mi último brote?"*, *"¿qué me ayuda más?"* |
| `/pain-import` | Import Apple Health XML exports from `data/imports/` |
| `/pain-schema` | View the current data schema and extras in use; promote frequent extras to formal fields |

### API reference

Full Swagger UI at `http://localhost:8420/docs`. Key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/entries` | Create a daily entry (pain, medication, mood, activity, stress, nutrition, extras) |
| `GET` | `/api/entries` | List entries (supports `?limit=N`, `?start_date=`, `?end_date=`) |
| `GET` | `/api/entries/{id}` | Get a single entry |
| `GET` | `/api/analysis/report` | Period report with stats, trends, and alerts (`?start_date=&end_date=`) |
| `GET` | `/api/analysis/correlation` | Correlation between two variables (`?var_a=pain_max&var_b=sleep_hours`) |
| `GET` | `/api/analysis/lag-correlation` | Lag analysis — is the effect immediate or next-day? (`?target=pain_max&variable=steps`) |
| `GET` | `/api/analysis/rankings` | Top factors that help or worsen pain |
| `POST` | `/api/weather/{date}` | Fetch and store weather for a date (optional `?city=CityName`) |
| `POST` | `/api/imports/apple-health` | Import Apple Health XML from `data/imports/` |

### Data model

Each daily entry can include:

- **Pain records** — location, intensity (0–10), pattern, time of day
- **Medication records** — name, dose, time taken, effectiveness (0–10)
- **Mood** — score (1–10), emotions
- **Activity records** — type, duration, effect on pain
- **Stress records** — level (1–10), source
- **Nutrition records** — meals, alcohol, caffeine, water intake
- **Extras** — arbitrary key-value pairs for tracking anything not in the standard schema (extras used 5+ times can be promoted to formal fields via `/pain-schema`)

Weather data (temperature, humidity, pressure, conditions) is fetched automatically during check-in.

Apple Health imports bring in: sleep hours, steps, resting heart rate, HRV, and sleep quality.

### Analysis variables

When querying correlations or asking questions, these are the variable names the system uses:

| Natural language | Variable name |
|---|---|
| sleep / sueño | `sleep_hours` |
| steps / pasos | `steps` |
| barometric pressure / presión | `pressure_hpa` / `pressure_change_hpa` |
| stress / estrés | `stress_level` |
| mood / ánimo | `mood_score` |
| exercise / actividad | `activity_minutes` / `activity_flag` |
| alcohol | `alcohol` |
| coffee / cafeína | `caffeine_cups` |
| medication effectiveness | `medication_effectiveness` |
| heart rate / frecuencia cardíaca | `resting_hr` |
| HRV / variabilidad | `hrv_ms` |

## Development

### Linting & Formatting

```bash
# Backend
cd backend && ruff check . && ruff format --check .

# Frontend
cd dashboard && npm run lint && npx tsc --noEmit
```

### Testing

```bash
cd backend && pytest --cov=backend
```

### Pre-commit Hooks

Husky + lint-staged run automatically on `git commit`:
- Python files: `ruff check --fix` + `ruff format`
- TypeScript/JavaScript files: `eslint --fix`

## Project Structure

```
pain-control/
├── backend/          # FastAPI API + analysis engine
│   ├── backend/      # Python package
│   │   ├── api/      # Routers, schemas, dependencies
│   │   ├── db/       # Models, migrations
│   │   ├── analysis/ # Trends, correlations, reports
│   │   └── importers/# Apple Health, weather
│   └── tests/        # pytest suite
├── dashboard/        # Next.js frontend
│   └── src/
│       ├── app/      # Pages (home, history, analysis)
│       ├── components/# UI components
│       ├── hooks/    # React Query hooks
│       └── lib/      # API client, utilities
├── data/             # SQLite database, imports
├── docs/             # Design specifications
└── skills/           # Claude Code skills
```

## License

MIT

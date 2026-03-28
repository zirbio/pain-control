# Pain Control

[![Backend CI](https://github.com/zirbio/pain-control/actions/workflows/backend.yml/badge.svg)](https://github.com/zirbio/pain-control/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/zirbio/pain-control/actions/workflows/frontend.yml/badge.svg)](https://github.com/zirbio/pain-control/actions/workflows/frontend.yml)

Personal chronic pain tracking and analysis system. Collects daily pain entries, medication, mood, activity, and health data to find patterns and correlations over time.

## Architecture

- **Backend**: Python 3.12 · FastAPI · SQLAlchemy · SQLite · Alembic
- **Frontend**: Next.js 16 · React 19 · TypeScript · Tailwind CSS 4 · shadcn/ui
- **Analysis**: Pandas · SciPy · correlation matrix · lag analysis · trend detection
- **Integrations**: Apple Health import · OpenWeatherMap

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn backend.api.main:app --reload
```

API available at `http://localhost:8000` — docs at `/docs`.

### Frontend

```bash
cd dashboard
npm install
npm run dev
```

Dashboard available at `http://localhost:3000`.

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

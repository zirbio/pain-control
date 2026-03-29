# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Personal chronic pain tracking system: daily check-ins (pain, medication, mood, activity, stress, nutrition) with statistical analysis for pattern detection. FastAPI backend + Next.js frontend + SQLite + Pandas/SciPy analysis engine.

## Commands

### Backend (working directory: `backend/`)

```bash
pip install -e ".[dev]"                          # Install with dev deps
uvicorn backend.api.main:app --reload --port 8000  # Dev server
ruff check .                                      # Lint
ruff format --check .                             # Format check
ruff check --fix . && ruff format .               # Auto-fix
pytest --cov=backend --cov-report=term-missing    # All tests + coverage
pytest tests/test_api_entries.py                  # Single test file
pytest tests/test_api_entries.py::test_create_entry  # Single test
pytest -k "test_correlations"                     # Pattern match
alembic upgrade head                              # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

### Frontend (working directory: `dashboard/`)

```bash
npm ci                  # Install deps
npm run dev             # Dev server (port 3000)
npm run lint            # ESLint
npx tsc --noEmit        # TypeScript check (must pass with 0 errors)
npm run build           # Production build
```

### Pre-commit (Husky + lint-staged)

Runs automatically on `git commit`:
- Python files: `ruff check --fix` + `ruff format`
- TS/JS files: `eslint --fix`

## Architecture

```
backend/backend/
  api/main.py          → FastAPI app, CORS, router registration
  api/routers/         → entries, imports, analysis, weather (all prefixed /api/)
  api/schemas.py       → Pydantic request/response models
  api/dependencies.py  → get_db session injection
  db/models.py         → SQLAlchemy models (daily_entries + child record tables)
  db/migrations/       → Alembic migrations
  analysis/            → correlations.py (Pearson + lag), trends.py, reports.py
  importers/           → Apple Health XML parser, weather fetcher
  core/config.py       → Pydantic Settings (env vars, defaults via model_post_init)

dashboard/src/
  app/                 → Next.js App Router pages (/, /history, /analysis, /coverage)
  components/          → React components (charts via Recharts/Nivo, UI via shadcn)
  hooks/               → React Query hooks (useEntries, useAnalysis)
  lib/api.ts           → API client (fetch wrapper, typed endpoints)
  lib/design-tokens.ts → Semantic color/typography tokens
```

## Key Patterns

**Data model**: All record tables (pain, medication, mood, activity, stress, nutrition, weather, apple_health, nutrition_import, workout) FK to `daily_entries` with `cascade="all, delete-orphan"`. One entry per date. The `extras` table stores arbitrary key-value pairs for schema evolution without migrations.

**Backend routers**: Each router uses `APIRouter(prefix="/api/...")` with `Depends(get_db)` for session injection. Entry creation uses `_populate_entry()` helper to bulk-assign nested records.

**Frontend data fetching**: TanStack React Query with custom hooks. Query keys follow `["resource", params]` pattern. API client at `lib/api.ts` defaults to `NEXT_PUBLIC_API_URL` or `http://localhost:8000`.

**Analysis engine**: Pearson correlation + p-value via `scipy.stats.pearsonr`. Supports lag analysis (does variable at day N correlate with pain at day N+1, N+2, etc.). Variables extracted from multiple record tables into flat dictionaries for computation.

**UI components**: shadcn/ui base + CVA variants + Tailwind CSS v4. Dark mode by default. Spanish locale for dates (`date-fns/locale/es`).

## Important Warnings

**Next.js version**: This project uses Next.js 16 which has breaking changes from earlier versions. Read `dashboard/node_modules/next/dist/docs/` before writing Next.js code. Do not assume APIs match your training data.

**Ruff ignores**: `B008` (FastAPI `Depends()` in function signatures) and `N806` (SQLAlchemy uppercase convention) are intentionally ignored.

**Database**: SQLite at `data/pain-control.db`. JSON fields (emotions, meals) are stored as serialized strings — manual serialization required.

**Weather**: Open-Meteo API (free, no auth key needed). Location defaults to Almería, Spain.

## CI Pipeline (must pass before merge)

**Backend** (`.github/workflows/backend.yml`): Python 3.12 → `ruff check .` → `ruff format --check .` → `pytest --cov`

**Frontend** (`.github/workflows/frontend.yml`): Node 22 → `npm run lint` → `npx tsc --noEmit` → `npm run build`

## Design Context

Full design documentation lives in `.impeccable.md`. Key points:

**Personality**: Clinical, precise, observational — a scientific instrument, not a lifestyle app.

**Theme**: "Warm Observatory" — dark mode only. Warm stone/terracotta palette (`#1c1917` bg). Avoids cold medical sterility while maintaining analytical precision.

**Reference**: Apple Health / Oura Ring — elegant data viz, premium feel, density without clutter.

**Typography**: Newsreader (serif) for metrics/headings + Satoshi (sans-serif) for body/labels. Numbers are primary content — large, legible, immediately scannable.

**Color language**: Pain scale gradient (sage `#6B8A7A` → terracotta `#8B2500`) is the foundational visual language. All color is semantic — amber warns, red alerts, sage reassures. Never cosmetic.

**Design principles**:
1. Data density over decoration — no ornamental elements
2. Semantic color, never cosmetic
3. Clinical warmth — precise but human
4. Glanceable metrics, explorable depth
5. Quiet confidence — subtle animations, calm competence

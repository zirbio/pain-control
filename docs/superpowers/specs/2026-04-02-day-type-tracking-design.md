# Day Type Tracking — Design Specification

**Date**: 2026-04-02
**Status**: Approved

## Context

Pain patterns likely correlate with daily routine structure. Workdays have fixed schedules (sleep, commute, desk time, stress patterns) while weekends and vacations differ significantly. Tracking day type as an explicit variable enables the correlation engine to detect and quantify these differences, and helps separate routine-driven pain from other factors.

## Requirements

- Three categories: `workday`, `weekend`, `vacation`
- Auto-detect workday vs weekend from date (Mon-Fri = workday, Sat-Sun = weekend)
- User can override to `vacation` manually
- Minimal friction: no extra question during daily check-in unless user mentions vacation
- Integrate with correlation engine for pattern analysis

## Design

### 1. Data Model

Add `day_type` column to `DailyEntry` in `backend/backend/db/models.py`:

```python
day_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

- **Type**: `String(20)` — consistent with `activity_pain_effect` pattern
- **Values**: `"workday"`, `"weekend"`, `"vacation"`
- **Validation**: Pydantic layer, not database (SQLite doesn't enforce Enum)

### 2. API Layer

**Schemas** (`backend/backend/api/schemas.py`):

`DailyEntryCreate`:
```python
day_type: str | None = None

@field_validator("day_type")
@classmethod
def validate_day_type(cls, v):
    if v is not None and v not in ("workday", "weekend", "vacation"):
        raise ValueError("day_type must be 'workday', 'weekend', or 'vacation'")
    return v
```

`DailyEntryResponse`:
```python
day_type: str | None = None
```

**Router** (`backend/backend/api/routers/entries.py`):

1. Add `"day_type"` to `_DIRECT_FIELDS`
2. Auto-detection after `_populate_entry()`:

```python
if entry.day_type is None:
    entry.day_type = "weekend" if data.date.weekday() >= 5 else "workday"
```

### 3. Analysis Integration

**One-hot encoding** in `build_daily_dataframe()` (`backend/backend/analysis/correlations.py`):

```python
day_type = entry.day_type
row["is_weekend"] = int(day_type == "weekend") if day_type else None
row["is_vacation"] = int(day_type == "vacation") if day_type else None
```

- `is_workday` is implicit (reference category) — avoids multicollinearity
- Numeric 0/1 columns flow through existing Spearman/Pearson engine unchanged
- Optional: day-type breakdown in reports (mean pain by day type)

### 4. Migration

Alembic migration: add column + backfill existing data.

```python
def upgrade():
    op.add_column("daily_entries", sa.Column("day_type", sa.String(20), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE daily_entries SET day_type = CASE "
        "WHEN strftime('%w', date) IN ('0', '6') THEN 'weekend' "
        "ELSE 'workday' END "
        "WHERE day_type IS NULL"
    ))

def downgrade():
    op.drop_column("daily_entries", "day_type")
```

### 5. Frontend

**Types** (`dashboard/src/lib/api.ts`): Add `day_type: string | null` to DailyEntry interface.

**Daily detail** (`dashboard/src/components/daily-detail.tsx`): Badge next to date header:
- "Vacaciones" (green) / "Fin de semana" (blue) / "Laborable" (muted, or hidden)
- Follow existing design token patterns

### 6. Check-in Skill

Update `.claude/skills/pain-checkin/SKILL.md`:
- Do NOT ask about day type — backend auto-detects
- Capture only when user mentions: "vacaciones", "día libre", "festivo" → `day_type: "vacation"`
- On entry update: preserve existing `day_type` in re-submission payload

## Verification

1. Run `alembic upgrade head` — migration applies without error
2. Check existing entries have backfilled `day_type` values
3. Create entry for a Monday without `day_type` → auto-detects `"workday"`
4. Create entry for a Saturday without `day_type` → auto-detects `"weekend"`
5. Create entry with `day_type: "vacation"` → preserved as-is
6. `pytest --cov` — all tests pass including new day_type tests
7. Correlation analysis includes `is_weekend` and `is_vacation` columns
8. Frontend shows day-type badge on entry detail
9. `ruff check .` + `npx tsc --noEmit` — zero errors

## Critical Files

- `backend/backend/db/models.py` — add column
- `backend/backend/api/schemas.py` — create + response schemas, validator
- `backend/backend/api/routers/entries.py` — `_DIRECT_FIELDS` + auto-detection
- `backend/backend/analysis/correlations.py` — one-hot encoding
- `dashboard/src/lib/api.ts` — TypeScript type
- `dashboard/src/components/daily-detail.tsx` — badge display
- `.claude/skills/pain-checkin/SKILL.md` — vacation capture

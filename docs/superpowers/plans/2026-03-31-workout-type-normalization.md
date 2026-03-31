# Workout Type Normalization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Normalize workout types from Spanish (Apple Health locale) to canonical English at import time, with a migration for existing data.

**Architecture:** Add a mapping dictionary and `normalize_workout_type()` function to the importer module. Apply normalization in `parse_workouts_csv()`. Create a data-only Alembic migration for existing records.

**Tech Stack:** Python, SQLAlchemy, Alembic, pytest

---

### Task 1: Add normalization function with tests (TDD)

**Files:**
- Modify: `backend/backend/importers/apple_health.py:1-7` (imports + new constant/function before classes)
- Modify: `backend/tests/test_apple_health.py` (add new tests)

- [ ] **Step 1: Write failing tests for `normalize_workout_type`**

Add to `backend/tests/test_apple_health.py`:

```python
from backend.importers.apple_health import normalize_workout_type


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_apple_health.py::test_normalize_workout_type_known_types tests/test_apple_health.py::test_normalize_workout_type_unknown_passthrough -v`

Expected: ImportError — `normalize_workout_type` does not exist yet.

- [ ] **Step 3: Implement the normalization function**

Add to `backend/backend/importers/apple_health.py` after the existing imports (line 6), before the dataclass definitions:

```python
import logging

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


def normalize_workout_type(raw_type: str) -> str:
    normalized = WORKOUT_TYPE_MAP.get(raw_type)
    if normalized is None:
        logger.warning("Unknown workout type: '%s' — storing as-is", raw_type)
        return raw_type
    return normalized
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_apple_health.py::test_normalize_workout_type_known_types tests/test_apple_health.py::test_normalize_workout_type_unknown_passthrough -v`

Expected: Both PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/backend/importers/apple_health.py backend/tests/test_apple_health.py
git commit -m "feat(importers): add workout type normalization function with tests"
```

---

### Task 2: Apply normalization in `parse_workouts_csv`

**Files:**
- Modify: `backend/backend/importers/apple_health.py:369` (workout_type assignment in `parse_workouts_csv`)
- Modify: `backend/tests/test_apple_health.py:156,164` (update existing test assertions)

- [ ] **Step 1: Update existing test assertions to expect normalized types**

In `backend/tests/test_apple_health.py`, function `test_parse_workouts_csv` (line ~156):

Change:
```python
    assert pilates.workout_type == "Pilates"
```
(This stays the same — "Pilates" maps to "Pilates".)

Change:
```python
    assert ciclismo.workout_type == "Interior Ciclismo"
```
To:
```python
    assert ciclismo.workout_type == "Indoor Cycling"
```

In `test_parse_workouts_csv_duration_two_parts` (line ~207), the test CSV uses "Walking" and "Running" as workout types. "Walking" is not in the map (the map has "Caminata" → "Walking"), and "Running" is not in the map either. These are already English — they'll pass through as-is via the fallback. No change needed.

- [ ] **Step 2: Run the updated test to verify it fails**

Run: `cd backend && pytest tests/test_apple_health.py::test_parse_workouts_csv -v`

Expected: FAIL — `assert "Interior Ciclismo" == "Indoor Cycling"`.

- [ ] **Step 3: Apply normalization in `parse_workouts_csv`**

In `backend/backend/importers/apple_health.py`, line 369, change:

```python
                        workout_type=workout_type,
```
To:
```python
                        workout_type=normalize_workout_type(workout_type),
```

- [ ] **Step 4: Run all workout-related tests**

Run: `cd backend && pytest tests/test_apple_health.py -k workout -v`

Expected: All PASS.

- [ ] **Step 5: Run full test suite**

Run: `cd backend && pytest --cov=backend --cov-report=term-missing`

Expected: All tests pass, no regressions.

- [ ] **Step 6: Commit**

```bash
git add backend/backend/importers/apple_health.py backend/tests/test_apple_health.py
git commit -m "feat(importers): apply workout type normalization in CSV parser"
```

---

### Task 3: Alembic migration for existing data

**Files:**
- Create: `backend/backend/db/migrations/versions/<auto>_normalize_workout_types.py` (via `alembic revision`)

- [ ] **Step 1: Create the migration**

Run: `cd backend && alembic revision -m "normalize workout types to english"`

- [ ] **Step 2: Write the migration logic**

In the generated migration file, replace the empty `upgrade()` and `downgrade()` with:

```python
from alembic import op

# Same mapping used in backend/importers/apple_health.py
_TYPE_MAP = {
    "Entrenamiento de Fuerza Funcional": "Rehabilitation",
    "Interior Ciclismo": "Indoor Cycling",
    "Caminata": "Walking",
    "Natación": "Swimming",
    "Ciclismo": "Cycling",
    "Elíptica": "Elliptical",
    "Estiramientos": "Stretching",
    "Golf": "Golf",
    # "Pilates" → "Pilates" and "Yoga" → "Yoga" are no-ops, skip them
}

_REVERSE_MAP = {v: k for k, v in _TYPE_MAP.items()}


def upgrade() -> None:
    conn = op.get_bind()
    for spanish, english in _TYPE_MAP.items():
        conn.execute(
            sa.text(
                "UPDATE workout_records SET workout_type = :new WHERE workout_type = :old"
            ),
            {"new": english, "old": spanish},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for english, spanish in _REVERSE_MAP.items():
        conn.execute(
            sa.text(
                "UPDATE workout_records SET workout_type = :new WHERE workout_type = :old"
            ),
            {"new": spanish, "old": english},
        )
```

Also add `import sqlalchemy as sa` to the imports at the top of the file.

- [ ] **Step 3: Run the migration**

Run: `cd backend && alembic upgrade head`

Expected: Migration applies successfully.

- [ ] **Step 4: Verify the data**

Run: `sqlite3 ../data/pain-control.db "SELECT DISTINCT workout_type FROM workout_records ORDER BY workout_type;"`

Expected:
```
Indoor Cycling
Pilates
Rehabilitation
```

- [ ] **Step 5: Test idempotency — run migration again**

Run: `cd backend && alembic downgrade -1 && alembic upgrade head`

Expected: Applies cleanly both ways. Same result.

- [ ] **Step 6: Run full test suite to confirm no regressions**

Run: `cd backend && pytest --cov=backend --cov-report=term-missing`

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/backend/db/migrations/versions/
git commit -m "feat(db): migrate existing workout types to normalized english names"
```

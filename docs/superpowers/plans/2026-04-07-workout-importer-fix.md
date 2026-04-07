# Workout Importer Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore end-to-end workout import from Apple Health so that (a) the 5 workout files already sitting in iCloud get backfilled, and (b) every future daily check-in pulls workouts automatically.

**Architecture:** Two complementary fixes to the Apple Health pipeline. (1) `parse_workouts_csv` is taught to detect and parse the new English-headered format (`Type`, `Active Energy (kJ)`, `Max Heart Rate (bpm)`, …) in addition to the old Spanish-headered one (`Workout Type`, `Energía Activa (kJ)`, …). When neither header matches, it raises a loud `ValueError` so future format drift fails fast instead of silently importing zero rows. (2) `scripts/health-auto-import.sh` is extended to also sync from the sibling iCloud folder `macOS-Silvio-Workouts/` where Health Auto Export now writes per-day workout CSVs.

**Tech Stack:** Python 3.12 · FastAPI · SQLAlchemy · pytest · Bash · Apple Health Auto Export (iCloud sync).

---

## Background — what's broken and why

Two latent breakages compound:

1. **Source folder split.** Until ~2026-03-28, Health Auto Export wrote a single `Workouts-<range>.csv` into `macOS-Silvio-Salud/`. Then it switched to writing one `Workouts-YYYY-MM-DD.csv` per day into a sibling folder `macOS-Silvio-Workouts/`. The sync script (`scripts/health-auto-import.sh:6`) only points at `macOS-Silvio-Salud/`, so the new files have never been copied into `data/imports/`.

2. **CSV header rename.** The new format also renamed every column. The parser at `backend/backend/importers/apple_health.py:360-406` filters every row because `row.get("Workout Type", "")` returns `""` for the new header `Type`, hitting the `if not workout_type … continue` guard. Result: 0 workouts imported, no exception, no log.

### Concrete column mapping (verified against the 5 unsynced files)

| Field             | Old (v1, Spanish)                  | New (v2, English)        |
| ----------------- | ---------------------------------- | ------------------------ |
| Type label        | `Workout Type`                     | `Type`                   |
| Active energy     | `Energía Activa (kJ)`              | `Active Energy (kJ)`     |
| Intensity         | `Intensidad (kcal/hr·kg)`          | *(absent)*               |
| Max HR            | `Frecuencia Cardíaca Máxima (bpm)` | `Max Heart Rate (bpm)`   |
| Avg HR            | `Frecuencia Cardíaca Promedio (bpm)` | `Avg Heart Rate (bpm)` |
| Distance          | `Distancia (km)`                   | `Distance (km)`          |
| Steps             | `Conteo de Pasos`                  | `Step Count (count)`     |
| Start / End / Duration | identical                     | identical                |

Workout type *values* (`Pilates`, `Interior Ciclismo`, `Entrenamiento de Fuerza Funcional`, `Golf`) are unchanged in both formats and are already covered by `WORKOUT_TYPE_MAP`.

### Workouts to recover (verified)

| Date       | File                                                                                  | Workout(s)                              |
| ---------- | ------------------------------------------------------------------------------------- | --------------------------------------- |
| 2026-03-23 | `~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/macOS-Silvio-Workouts/Workouts-2026-03-23.csv` | Pilates                                 |
| 2026-03-26 | `…/macOS-Silvio-Workouts/Workouts-2026-03-26.csv`                                    | Entrenamiento de Fuerza Funcional       |
| 2026-04-03 | `…/macOS-Silvio-Workouts/Workouts-2026-04-03.csv`                                    | Golf                                    |
| 2026-04-05 | `…/macOS-Silvio-Workouts/Workouts-2026-04-05.csv`                                    | Interior Ciclismo                       |
| 2026-04-06 | `…/macOS-Silvio-Workouts/Workouts-2026-04-06.csv`                                    | Golf, Pilates                           |

The persist function (`backend/backend/api/routers/imports.py:80-101`) is already idempotent — it deletes existing `WorkoutRecord`s for a date before re-inserting — so the 23-mar / 26-mar rows already in the DB from the old combined file will be cleanly replaced by the v2 rows.

---

## File Structure

**Modify:**
- `backend/backend/importers/apple_health.py` — add v1/v2 column maps; rewrite `parse_workouts_csv` to detect format from header and raise on unknown formats.
- `backend/tests/test_apple_health.py` — add three new tests covering v2 happy path, v2 missing-intensity behaviour, and unknown-header error.
- `scripts/health-auto-import.sh` — add `ICLOUD_WORKOUTS_DIR` and a second copy loop. Rename the existing `ICLOUD_DIR` to `ICLOUD_HEALTH_DIR` for clarity.

**No new files.** No DB migration (the model already accommodates `intensity=None`).

---

## Task 1: Set up working branch

**Files:** *(none — git only)*

- [ ] **Step 1: Create feature branch from main**

```bash
cd /Users/silvio_requena/Code/pain-control
git checkout main
git pull --ff-only
git checkout -b fix/workout-importer-format-and-sync
```

- [ ] **Step 2: Confirm clean tree**

Run: `git status`
Expected: `nothing to commit, working tree clean`

---

## Task 2: Failing test for v2 (English) workout format

**Files:**
- Test: `backend/tests/test_apple_health.py` *(append at end of file, after `test_normalize_workout_type_unknown_passthrough`)*

- [ ] **Step 1: Append the failing test**

Append to `backend/tests/test_apple_health.py`:

```python


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
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `cd backend && pytest tests/test_apple_health.py::test_parse_workouts_csv_v2_english_format -v`

Expected: FAIL — `assert len(workouts) == 2` fails because `len(workouts) == 0` (every row is filtered out by the `if not workout_type` guard, since `row.get("Workout Type", "")` returns `""` for v2 headers).

---

## Task 3: Failing test for unrecognized workout CSV header

**Files:**
- Test: `backend/tests/test_apple_health.py` *(append after the v2 test)*

- [ ] **Step 1: Append the failing test**

Append to `backend/tests/test_apple_health.py`:

```python


def test_parse_workouts_csv_unknown_header_raises(tmp_path):
    """Unknown header schema must raise loudly, not silently return []."""
    csv_file = tmp_path / "Workouts-future.csv"
    csv_file.write_text(
        "Activity,Started,Ended,Length\n"
        "Yoga,2026-05-01 08:00,2026-05-01 08:45,45:00\n"
    )
    importer = AppleHealthImporter()
    with pytest.raises(ValueError, match="Unrecognized workout CSV header"):
        importer.parse_workouts_csv(csv_file)
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `cd backend && pytest tests/test_apple_health.py::test_parse_workouts_csv_unknown_header_raises -v`

Expected: FAIL — `DID NOT RAISE <class 'ValueError'>`. The current parser silently returns `[]` for unknown headers.

---

## Task 4: Implement v2 parser support + format detection

**Files:**
- Modify: `backend/backend/importers/apple_health.py` *(replace the entire `parse_workouts_csv` method, lines 360-406, and add module-level constants near `WORKOUT_TYPE_MAP`)*

- [ ] **Step 1: Add v1/v2 column-map constants**

In `backend/backend/importers/apple_health.py`, immediately after the `WORKOUT_TYPE_MAP` block (after line 22, before `def normalize_workout_type`), insert:

```python
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
```

- [ ] **Step 2: Replace `parse_workouts_csv` with format-aware version**

Replace the existing `parse_workouts_csv` method (currently at lines 360-406) with:

```python
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
                date = start_time.date()

                end_str = row.get("End", "").strip()
                end_time: datetime.datetime | None = None
                if end_str:
                    end_time = _parse_flexible_datetime(end_str)

                duration_str = row.get("Duration", "").strip()
                duration_min: float | None = None
                if duration_str:
                    parts = duration_str.split(":")
                    if len(parts) == 3:
                        h, m, s = (float(p) for p in parts)
                        duration_min = h * 60 + m + s / 60
                    elif len(parts) == 2:
                        m, s = (float(p) for p in parts)
                        duration_min = m + s / 60

                intensity_col = cols.get("intensity")
                intensity = (
                    self._row_float(row, intensity_col) if intensity_col else None
                )

                results.append(
                    WorkoutData(
                        date=date,
                        workout_type=normalize_workout_type(workout_type),
                        start_time=start_time,
                        end_time=end_time,
                        duration_min=(round(duration_min, 1) if duration_min is not None else None),
                        active_energy_kj=self._row_float(row, cols["active_energy_kj"]),
                        intensity=intensity,
                        max_hr=self._row_int(row, cols["max_hr"]),
                        avg_hr=self._row_int(row, cols["avg_hr"]),
                        distance_km=self._row_float(row, cols["distance_km"]),
                        steps=self._row_int(row, cols["steps"]),
                    )
                )

        return results
```

- [ ] **Step 3: Run both new tests and verify they pass**

Run: `cd backend && pytest tests/test_apple_health.py::test_parse_workouts_csv_v2_english_format tests/test_apple_health.py::test_parse_workouts_csv_unknown_header_raises -v`

Expected: 2 passed.

- [ ] **Step 4: Run the full apple_health test module to verify no regression**

Run: `cd backend && pytest tests/test_apple_health.py -v`

Expected: all tests pass (the v1 tests `test_parse_workouts_csv`, `test_parse_workouts_csv_duration_two_parts`, `test_parse_workouts_csv_empty_file` still cover the legacy Spanish path; the empty-file test still passes because its header `"Workout Type,Start,End,Duration,Energía Activa (kJ)"` triggers v1).

- [ ] **Step 5: Lint and format**

Run: `cd backend && ruff check --fix . && ruff format .`

Expected: no remaining errors.

- [ ] **Step 6: Commit the parser fix**

```bash
cd /Users/silvio_requena/Code/pain-control
git add backend/backend/importers/apple_health.py backend/tests/test_apple_health.py
git commit -m "$(cat <<'EOF'
feat(importers): support new English workout CSV format

Health Auto Export switched workout exports from Spanish-headered
combined CSVs to English-headered per-day files (~2026-03-28). The
parser silently dropped every row because it only knew "Workout Type",
not "Type". Now detects format from headers, supports both v1 and v2,
and raises ValueError on unknown schemas to fail fast on future drift.
EOF
)"
```

Expected: pre-commit hook (ruff) passes, commit succeeds.

---

## Task 5: Update sync script to also copy from `macOS-Silvio-Workouts/`

**Files:**
- Modify: `scripts/health-auto-import.sh`

- [ ] **Step 1: Replace the iCloud path block + copy loop**

Replace lines 5-36 of `scripts/health-auto-import.sh` (from `PROJECT_DIR=` through the end of the copy loop) with:

```bash
PROJECT_DIR="/Users/silvio_requena/Code/pain-control"
ICLOUD_HEALTH_DIR="$HOME/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/macOS-Silvio-Salud"
ICLOUD_WORKOUTS_DIR="$HOME/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/macOS-Silvio-Workouts"
IMPORTS_DIR="$PROJECT_DIR/data/imports"
LOG_FILE="$PROJECT_DIR/data/logs/auto-import.log"
API_URL="http://127.0.0.1:8420/api/imports/apple-health"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Ensure imports dir exists
mkdir -p "$IMPORTS_DIR"

# Check source folders exist
if [ ! -d "$ICLOUD_HEALTH_DIR" ]; then
    log "ERROR: iCloud health folder not found: $ICLOUD_HEALTH_DIR"
    exit 1
fi
if [ ! -d "$ICLOUD_WORKOUTS_DIR" ]; then
    log "WARN: iCloud workouts folder not found: $ICLOUD_WORKOUTS_DIR"
fi

# Copy new CSV files (skip if already present in imports)
copied=0
sync_dir() {
    local src_dir="$1"
    local pattern="$2"
    [ -d "$src_dir" ] || return 0
    for src_file in "$src_dir"/$pattern; do
        [ -f "$src_file" ] || continue
        filename=$(basename "$src_file")
        dest_file="$IMPORTS_DIR/$filename"
        if [ ! -f "$dest_file" ] || [ "$src_file" -nt "$dest_file" ]; then
            cp "$src_file" "$dest_file"
            log "COPIED: $filename"
            copied=$((copied + 1))
        fi
    done
}

sync_dir "$ICLOUD_HEALTH_DIR" "HealthMetrics-*.csv"
sync_dir "$ICLOUD_WORKOUTS_DIR" "Workouts-*.csv"
```

- [ ] **Step 2: Verify the script still parses (`bash -n`)**

Run: `bash -n scripts/health-auto-import.sh`

Expected: no output (script syntax is valid).

- [ ] **Step 3: Dry-run the script and confirm it copies the 5 missing files**

First confirm the imports dir does **not** yet contain `Workouts-2026-*.csv`:

Run: `ls data/imports/Workouts-2026-*.csv 2>/dev/null; echo "exit=$?"`
Expected: `exit=2` (no such files).

Then run:

```bash
bash scripts/health-auto-import.sh
```

Expected behavior:
- The 5 v2 workout files appear in `data/imports/`.
- The script proceeds to call the import API (if backend is running on `:8420`) or exits with `WARN: Backend not running …`.

Verify the files landed:

Run: `ls data/imports/Workouts-2026-*.csv`

Expected:
```
data/imports/Workouts-2026-03-23.csv
data/imports/Workouts-2026-03-26.csv
data/imports/Workouts-2026-04-03.csv
data/imports/Workouts-2026-04-05.csv
data/imports/Workouts-2026-04-06.csv
```

- [ ] **Step 4: Tail the log and confirm**

Run: `tail -20 data/logs/auto-import.log`

Expected: 5 fresh `COPIED:` lines for the workout files, then either an `IMPORT OK:` line or a `WARN: Backend not running …` line.

- [ ] **Step 5: Commit the script change**

```bash
cd /Users/silvio_requena/Code/pain-control
git add scripts/health-auto-import.sh
git commit -m "$(cat <<'EOF'
chore(scripts): sync workouts from separate iCloud subfolder

Health Auto Export now writes workout CSVs to a sibling folder
(macOS-Silvio-Workouts) instead of macOS-Silvio-Salud. Add a second
sync pass so per-day Workouts-YYYY-MM-DD.csv files reach data/imports.
EOF
)"
```

Expected: commit succeeds.

---

## Task 6: Backfill the 5 missing workout files end-to-end

**Files:** *(none — runtime verification only)*

- [ ] **Step 1: Make sure the backend is running**

Run: `curl -sf http://127.0.0.1:8420/api/health && echo OK`

Expected: `OK`.

If it prints nothing, start the backend in another terminal:

```bash
cd backend && uvicorn backend.api.main:app --reload --port 8420
```

…then re-run the curl check.

- [ ] **Step 2: Trigger the import endpoint directly**

Run:

```bash
curl -sf -X POST http://127.0.0.1:8420/api/imports/apple-health | python3 -m json.tool
```

Expected (numbers may vary slightly depending on what's already in `data/imports/`):
- `errors`: empty list `[]`
- `workouts_imported`: at least 6 (Pilates 23-mar, Fuerza 26-mar, Golf 3-abr, Ciclismo 5-abr, Golf 6-abr, Pilates 6-abr).
- `files_processed`: increased by 5 vs. before.

If `errors` is non-empty, **stop and investigate** — do not proceed.

- [ ] **Step 3: Verify each date in the API**

Run, for each date:

```bash
for d in 2026-03-23 2026-03-26 2026-04-03 2026-04-05 2026-04-06; do
  echo "=== $d ==="
  curl -sf "http://127.0.0.1:8420/api/entries/$d" \
    | python3 -c "import sys, json; e = json.load(sys.stdin); print([(w['workout_type'], w.get('start_time')) for w in e.get('workout_records', [])])"
done
```

Expected output:
```
=== 2026-03-23 ===
[('Pilates', '2026-03-23T09:04:00')]
=== 2026-03-26 ===
[('Rehabilitation', '2026-03-26T13:03:00')]
=== 2026-04-03 ===
[('Golf', '2026-04-03T11:09:00')]
=== 2026-04-05 ===
[('Indoor Cycling', '2026-04-05T16:14:00')]
=== 2026-04-06 ===
[('Golf', '2026-04-06T16:32:00'), ('Pilates', '2026-04-06T09:03:00')]
```

(Order within a day may differ — the assertion is "both Golf and Pilates appear on 2026-04-06".)

- [ ] **Step 4: Re-run the script idempotently and confirm no duplicates**

Run: `bash scripts/health-auto-import.sh`

Expected log line: `No new files to import` (mtimes haven't changed since last copy).

Re-query 2026-04-06:

```bash
curl -sf http://127.0.0.1:8420/api/entries/2026-04-06 \
  | python3 -c "import sys, json; print(len(json.load(sys.stdin)['workout_records']))"
```

Expected: `2` (still two rows, not four — the persist function deletes-then-inserts so re-imports are idempotent).

---

## Task 7: Full pre-push verification

**Files:** *(none — verification only)*

- [ ] **Step 1: Run the complete backend test suite with coverage**

Run: `cd backend && pytest --cov=backend --cov-report=term-missing`

Expected: all tests pass. Note coverage on `backend/importers/apple_health.py` should not drop.

- [ ] **Step 2: Run ruff check + format check (mirrors CI)**

Run: `cd backend && ruff check . && ruff format --check .`

Expected: no errors, no diff.

- [ ] **Step 3: Verify git log**

Run: `git log --oneline main..HEAD`

Expected: exactly two commits:
```
<sha2> chore(scripts): sync workouts from separate iCloud subfolder
<sha1> feat(importers): support new English workout CSV format
```

- [ ] **Step 4: Push the branch**

Run:

```bash
git push -u origin fix/workout-importer-format-and-sync
```

Expected: branch pushed, remote tracking set.

- [ ] **Step 5: Open the PR**

Run:

```bash
gh pr create --title "fix(importers): restore workout sync after Health Auto Export format change" --body "$(cat <<'EOF'
## Summary
- Teach `parse_workouts_csv` to handle the new English-headered v2 format that Health Auto Export started writing around 2026-03-28, while keeping the old Spanish-headered v1 path working
- Raise `ValueError` on any unknown workout CSV header so future format drift fails loudly instead of silently importing zero rows
- Extend `scripts/health-auto-import.sh` to also sync from the sibling iCloud folder `macOS-Silvio-Workouts/` where v2 files are written

## Why
Since 2026-03-28 the daily check-ins have been silently missing workout data — confirmed by 5 unsynced workout files sitting in iCloud (Pilates, Fuerza Funcional, two Golf rounds, an Interior Ciclismo session, plus a 6-abr Pilates) that never reached the DB. Both the source folder *and* the column headers had changed, and the failure was double-silent: the script didn't see the files, and the parser would have dropped every row anyway.

## Test plan
- [x] New unit test: `test_parse_workouts_csv_v2_english_format` covers v2 happy path including missing-intensity behaviour
- [x] New unit test: `test_parse_workouts_csv_unknown_header_raises` ensures schema drift fails fast
- [x] Existing v1 tests still pass (legacy Spanish format unchanged)
- [x] Manually backfilled the 5 missing files via `POST /api/imports/apple-health`; confirmed all 6 workouts visible at `/api/entries/{date}`
- [x] Re-ran sync script to confirm idempotency (no duplicate `WorkoutRecord`s)
EOF
)"
```

Expected: PR created, URL printed.

---

## Self-Review Checklist (run before considering plan complete)

- [x] **Spec coverage:** Both user requirements covered — backfill of existing files (Task 6) and future check-ins working automatically (Tasks 4 + 5 together).
- [x] **No placeholders:** Every code block contains actual code; every command has expected output.
- [x] **Type consistency:** `WORKOUT_COLUMNS_V1` / `V2` keys match exactly between the constants definition (Task 4 Step 1) and the parser usage (Task 4 Step 2). `intensity` is intentionally absent from `V2` and the parser uses `cols.get("intensity")` to handle that.
- [x] **Idempotency considered:** Persist function already deletes-then-inserts per date; verified explicitly in Task 6 Step 4.
- [x] **Failure modes:** Unknown header now raises (Task 3 + Task 4); endpoint already wraps each file in try/except and surfaces errors in the JSON response.

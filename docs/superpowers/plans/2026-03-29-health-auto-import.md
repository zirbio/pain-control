# Health Auto Import Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically import Health Auto Export CSVs from iCloud Drive into the pain-control database whenever new files appear.

**Architecture:** A shell script copies new CSVs from the iCloud Drive folder to `data/imports/` (skipping already-imported files), then calls the existing import API endpoint. A `launchd` agent with `WatchPaths` triggers the script whenever the iCloud folder changes. The backend importer glob is widened to also match the `HealthMetrics-*.csv` naming convention from Health Auto Export's automation feature.

**Tech Stack:** Bash, launchd (WatchPaths), curl, existing FastAPI import endpoint on port 8420.

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `scripts/health-auto-import.sh` | Copy new CSVs from iCloud → `data/imports/`, call import API |
| Create | `scripts/com.pain-control.auto-import.plist` | launchd agent definition with WatchPaths |
| Modify | `backend/backend/api/routers/imports.py:111` | Add `HealthMetrics-*.csv` to glob pattern |
| Modify | `backend/tests/test_api_imports.py` | Add test for `HealthMetrics-*.csv` file name |

---

### Task 1: Widen the importer glob to match `HealthMetrics-*.csv`

**Files:**
- Modify: `backend/tests/test_api_imports.py`
- Modify: `backend/backend/api/routers/imports.py:111`

- [ ] **Step 1: Write failing test for HealthMetrics-*.csv import**

Add a new test fixture and test that uses the `HealthMetrics-` prefix instead of `HealthAutoExport-`:

```python
# Add after the existing client_with_csv_imports fixture (line 113)

@pytest.fixture()
def client_with_healthmetrics_csv(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    imports_dir = tmp_path / "imports"
    imports_dir.mkdir()

    csv_content = (
        "Fecha/Hora,Energía Activa (kJ),Frecuencia Cardiaca en Reposo (bpm),"
        "Variabilidad de Frecuencia Cardíaca (ms)\n"
        "2026-03-28 00:00,1300,58,48.7\n"
    )
    (imports_dir / "HealthMetrics-2026-03-28.csv").write_text(csv_content)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("backend.api.routers.imports.get_imports_dir", lambda: str(imports_dir))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_import_healthmetrics_csv(client_with_healthmetrics_csv):
    """HealthMetrics-*.csv files (Health Auto Export naming) are imported."""
    response = client_with_healthmetrics_csv.post("/api/imports/apple-health")
    assert response.status_code == 200
    data = response.json()
    assert data["files_processed"] == 1
    assert data["days_imported"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/silvio_requena/Code/pain-control/backend && uv run pytest tests/test_api_imports.py::test_import_healthmetrics_csv -v`

Expected: FAIL — `assert data["files_processed"] == 1` fails because the glob doesn't match `HealthMetrics-*.csv`.

- [ ] **Step 3: Add HealthMetrics glob to importer**

In `backend/backend/api/routers/imports.py`, change line 111 from:

```python
    csv_files = list(imports_dir.glob("HealthAutoExport-*.csv"))
```

to:

```python
    csv_files = list(imports_dir.glob("HealthAutoExport-*.csv")) + list(
        imports_dir.glob("HealthMetrics-*.csv")
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/silvio_requena/Code/pain-control/backend && uv run pytest tests/test_api_imports.py -v`

Expected: ALL tests pass, including the new `test_import_healthmetrics_csv`.

- [ ] **Step 5: Commit**

```bash
git add backend/backend/api/routers/imports.py backend/tests/test_api_imports.py
git commit -m "feat(import): support HealthMetrics-*.csv naming from Health Auto Export"
```

---

### Task 2: Create the auto-import shell script

**Files:**
- Create: `scripts/health-auto-import.sh`

The script must:
1. Copy only NEW files (not already in `data/imports/`) from iCloud Drive
2. Check if the backend is running before calling the API
3. Log everything to `data/logs/auto-import.log`
4. Exit cleanly if nothing to do

- [ ] **Step 1: Create the scripts directory**

```bash
mkdir -p /Users/silvio_requena/Code/pain-control/scripts
```

- [ ] **Step 2: Write the auto-import script**

Create `scripts/health-auto-import.sh`:

```bash
#!/bin/bash
# health-auto-import.sh — Copy new Health Auto Export CSVs and trigger import
set -euo pipefail

PROJECT_DIR="/Users/silvio_requena/Code/pain-control"
ICLOUD_DIR="$HOME/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/macOS-Silvio-Salud"
IMPORTS_DIR="$PROJECT_DIR/data/imports"
LOG_FILE="$PROJECT_DIR/data/logs/auto-import.log"
API_URL="http://127.0.0.1:8420/api/imports/apple-health"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Ensure imports dir exists
mkdir -p "$IMPORTS_DIR"

# Check source folder exists
if [ ! -d "$ICLOUD_DIR" ]; then
    log "ERROR: iCloud folder not found: $ICLOUD_DIR"
    exit 1
fi

# Copy new CSV files (skip if already present in imports)
copied=0
for src_file in "$ICLOUD_DIR"/HealthMetrics-*.csv "$ICLOUD_DIR"/Workouts-*.csv; do
    [ -f "$src_file" ] || continue
    filename=$(basename "$src_file")
    dest_file="$IMPORTS_DIR/$filename"

    if [ ! -f "$dest_file" ] || [ "$src_file" -nt "$dest_file" ]; then
        cp "$src_file" "$dest_file"
        log "COPIED: $filename"
        copied=$((copied + 1))
    fi
done

if [ "$copied" -eq 0 ]; then
    log "No new files to import"
    exit 0
fi

log "Copied $copied file(s), triggering import..."

# Check if backend is running
if ! curl -sf http://127.0.0.1:8420/api/health > /dev/null 2>&1; then
    log "WARN: Backend not running on port 8420 — skipping API call. Files copied for next manual import."
    exit 0
fi

# Trigger import
response=$(curl -sf -X POST "$API_URL" 2>&1) || {
    log "ERROR: Import API call failed"
    exit 1
}

log "IMPORT OK: $response"
```

- [ ] **Step 3: Make the script executable**

```bash
chmod +x /Users/silvio_requena/Code/pain-control/scripts/health-auto-import.sh
```

- [ ] **Step 4: Test the script manually**

```bash
/Users/silvio_requena/Code/pain-control/scripts/health-auto-import.sh
cat /Users/silvio_requena/Code/pain-control/data/logs/auto-import.log
```

Expected: Log shows files copied and import result (or backend-not-running warning if the service is down).

- [ ] **Step 5: Commit**

```bash
git add scripts/health-auto-import.sh
git commit -m "feat(import): add auto-import script for iCloud Health Auto Export CSVs"
```

---

### Task 3: Create the launchd agent

**Files:**
- Create: `scripts/com.pain-control.auto-import.plist`

The agent uses `WatchPaths` to monitor the iCloud folder. When files change, it runs the import script. `ThrottleInterval` prevents rapid re-fires during iCloud sync bursts.

- [ ] **Step 1: Write the launchd plist**

Create `scripts/com.pain-control.auto-import.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pain-control.auto-import</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/silvio_requena/Code/pain-control/scripts/health-auto-import.sh</string>
    </array>
    <key>WatchPaths</key>
    <array>
        <string>/Users/silvio_requena/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/macOS-Silvio-Salud</string>
    </array>
    <key>ThrottleInterval</key>
    <integer>60</integer>
    <key>StandardOutPath</key>
    <string>/Users/silvio_requena/Code/pain-control/data/logs/auto-import.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/silvio_requena/Code/pain-control/data/logs/auto-import.stderr.log</string>
</dict>
</plist>
```

- [ ] **Step 2: Symlink the plist into LaunchAgents**

```bash
ln -sf /Users/silvio_requena/Code/pain-control/scripts/com.pain-control.auto-import.plist ~/Library/LaunchAgents/com.pain-control.auto-import.plist
```

- [ ] **Step 3: Load the agent**

```bash
launchctl load ~/Library/LaunchAgents/com.pain-control.auto-import.plist
```

Verify it's loaded:

```bash
launchctl list | grep pain-control.auto-import
```

Expected: Shows the agent with PID `-` (waiting for trigger) and status `0`.

- [ ] **Step 4: Test the WatchPaths trigger**

Create a dummy file in the iCloud folder to trigger the watcher:

```bash
touch ~/Library/Mobile\ Documents/iCloud~com~ifunography~HealthExport/Documents/macOS-Silvio-Salud/.trigger-test
```

Wait ~60 seconds (ThrottleInterval), then check:

```bash
cat /Users/silvio_requena/Code/pain-control/data/logs/auto-import.log
```

Expected: Log entry showing the script ran (either "No new files" or files copied).

Clean up the trigger file:

```bash
rm ~/Library/Mobile\ Documents/iCloud~com~ifunography~HealthExport/Documents/macOS-Silvio-Salud/.trigger-test
```

- [ ] **Step 5: Commit**

```bash
git add scripts/com.pain-control.auto-import.plist
git commit -m "feat(import): add launchd agent to auto-import on iCloud sync"
```

---

### Task 4: Add scripts/ to .gitignore review and update docs

**Files:**
- Verify: `.gitignore` (no changes expected — scripts/ should be tracked)

- [ ] **Step 1: Verify .gitignore doesn't exclude scripts/**

```bash
cd /Users/silvio_requena/Code/pain-control && git check-ignore scripts/health-auto-import.sh
```

Expected: No output (file is NOT ignored).

- [ ] **Step 2: Run full test suite**

```bash
cd /Users/silvio_requena/Code/pain-control/backend && uv run pytest -v
```

Expected: All tests pass, including the new `test_import_healthmetrics_csv`.

- [ ] **Step 3: Verify TypeScript compilation (frontend unchanged but verify)**

```bash
cd /Users/silvio_requena/Code/pain-control/dashboard && npx tsc --noEmit
```

Expected: 0 errors.

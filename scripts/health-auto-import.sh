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

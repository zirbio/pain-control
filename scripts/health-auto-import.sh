#!/bin/bash
# health-auto-import.sh — Copy new Health Auto Export CSVs and trigger import.
#
# Companion launchd agent: scripts/com.pain-control.auto-import.plist
# When you change WatchPaths in the plist, redeploy with:
#   cp scripts/com.pain-control.auto-import.plist ~/Library/LaunchAgents/
#   launchctl unload ~/Library/LaunchAgents/com.pain-control.auto-import.plist
#   launchctl load ~/Library/LaunchAgents/com.pain-control.auto-import.plist
set -euo pipefail

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

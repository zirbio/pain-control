# Pain Control Launcher — Design Spec

macOS launcher for Pain Control using `launchd` agents with a CLI and double-click `.command` file.

## Components

### 1. `bin/pain-control` (bash CLI)

Subcommands: `start`, `stop`, `restart`, `status`, `logs api|web`, `open`, `install`, `uninstall`.

- `start`: loads both plist agents via `launchctl bootstrap`
- `stop`: unloads both agents via `launchctl bootout`
- `restart`: stop + start
- `status`: checks if agents are loaded, shows PIDs and ports
- `logs api`: `tail -f data/logs/backend.log`
- `logs web`: `tail -f data/logs/dashboard.log`
- `open`: opens `http://localhost:3001` in default browser
- `install`: copies plists to `~/Library/LaunchAgents/`
- `uninstall`: stops services and removes plists from `~/Library/LaunchAgents/`

### 2. `pain-control.command` (Finder double-click)

Wrapper that opens a terminal with an interactive menu calling `bin/pain-control` subcommands. Menu options: Start all, Stop all, Restart all, Status, Logs (backend), Logs (dashboard), Open dashboard, Quit.

### 3. `launchd/com.pain-control.backend.plist`

- Runs: `backend/.venv/bin/uvicorn backend.api.main:app --host 127.0.0.1 --port 8420`
- WorkingDirectory: `<PROJECT_ROOT>/backend`
- Logs: `data/logs/backend.log`, `data/logs/backend.error.log`
- KeepAlive: false
- RunAtLoad: false

### 4. `launchd/com.pain-control.dashboard.plist`

- Runs: `npx next start --port 3001` (production) or `npm run dev -- --port 3001`
- WorkingDirectory: `<PROJECT_ROOT>/dashboard`
- Logs: `data/logs/dashboard.log`, `data/logs/dashboard.error.log`
- KeepAlive: false
- RunAtLoad: false

## Configuration updates

- `dashboard/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8420`
- `backend/.env` or config: CORS includes `http://localhost:3001`

## Ports

| Service | Port |
|---|---|
| Backend API | 8420 |
| Dashboard | 3001 |

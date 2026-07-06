#!/usr/bin/env bash
# Starts the Echo Base backend and frontend together for local
# development/testing.
#
# The backend host/port come from the app's own config loader --
# config/config.yaml, then ECHO_BASE_SERVER__HOST/PORT env vars, then
# built-in defaults (8088) -- so this script never drifts out of sync
# with what `uvicorn app.main:app` actually binds to.
#
# Usage:
#   ./start.sh                              # uses config/config.yaml (or defaults)
#   ECHO_BASE_BACKEND_PORT=8811 ./start.sh   # force a port for this run only
#   ECHO_BASE_FRONTEND_PORT=5174 ./start.sh
#
# Ctrl+C stops both. Frontend dependencies are installed automatically
# on first run (via npm if available, otherwise via a rootless podman
# Node container -- see docs/INSTALL.md).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

FRONTEND_PORT="${ECHO_BASE_FRONTEND_PORT:-5173}"

VENV_DIR="$ROOT_DIR/.venv"
BACKEND_LOG="$ROOT_DIR/logs/backend.out.log"
mkdir -p "$ROOT_DIR/logs"

echo "== Echo Base dev launcher =="

# --- Backend: create venv + install deps on first run ---
if [ ! -d "$VENV_DIR" ]; then
  echo "-> Creating Python virtualenv at .venv"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -U pip -q
  "$VENV_DIR/bin/pip" install -r backend/requirements.txt -q
elif ! "$VENV_DIR/bin/python" -c "import fastapi" >/dev/null 2>&1; then
  echo "-> Installing backend dependencies"
  "$VENV_DIR/bin/pip" install -r backend/requirements.txt -q
fi

# A script-level port override forces the backend to actually bind to
# that port too, so the two can't disagree.
if [ -n "${ECHO_BASE_BACKEND_PORT:-}" ]; then
  export ECHO_BASE_SERVER__PORT="$ECHO_BASE_BACKEND_PORT"
fi

# Resolve the effective host/port/allowed-hosts the same way the app
# does (config.yaml > ECHO_BASE_* env vars > defaults) instead of
# re-implementing YAML parsing here.
read -r BACKEND_HOST BACKEND_PORT ALLOWED_HOSTS_CSV <<<"$(
  cd "$ROOT_DIR/backend"
  "$VENV_DIR/bin/python" -c "
from app.core.config import get_settings
s = get_settings().server
print(s.host, s.port, ','.join(s.allowed_hosts))
"
)"

# A 0.0.0.0 bind address is fine for uvicorn but not something to curl
# or proxy to directly -- talk to loopback for that.
BACKEND_CONNECT_HOST="$BACKEND_HOST"
if [ "$BACKEND_CONNECT_HOST" = "0.0.0.0" ]; then
  BACKEND_CONNECT_HOST="127.0.0.1"
fi

echo "-> Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT}"
(
  cd "$ROOT_DIR/backend"
  # Unbuffered so the first-run admin password (printed, not logged)
  # actually lands in the log file promptly instead of sitting in a
  # stdout buffer.
  export PYTHONUNBUFFERED=1
  exec "$VENV_DIR/bin/uvicorn" app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
) >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

cleanup() {
  echo
  echo "-> Stopping..."
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
  wait "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait for the backend to come up (or fail fast with a useful message).
echo -n "-> Waiting for backend health check"
for _ in $(seq 1 30); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo
    echo "Backend process exited early. Last log lines:"
    tail -n 30 "$BACKEND_LOG" || true
    exit 1
  fi
  if curl -sf "http://${BACKEND_CONNECT_HOST}:${BACKEND_PORT}/api/system/health" >/dev/null 2>&1; then
    echo " ok"
    break
  fi
  echo -n "."
  sleep 1
done

if grep -q "^   password: " "$BACKEND_LOG" 2>/dev/null; then
  echo
  echo "== First run: a default administrator account was created =="
  grep -E "^   username: |^   password: " "$BACKEND_LOG" || true
  echo
fi

# --- Frontend: install deps + run dev server ---
cd "$ROOT_DIR/frontend"

export ECHO_BASE_BACKEND_HOST="$BACKEND_CONNECT_HOST"
export ECHO_BASE_BACKEND_PORT="$BACKEND_PORT"
export ECHO_BASE_ALLOWED_HOSTS="$ALLOWED_HOSTS_CSV"

if command -v npm >/dev/null 2>&1; then
  if [ ! -d node_modules ]; then
    echo "-> Installing frontend dependencies (npm)"
    npm install
  fi
  echo "-> Starting frontend on http://localhost:${FRONTEND_PORT} (npm)"
  npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
elif command -v podman >/dev/null 2>&1; then
  if [ ! -d node_modules ]; then
    echo "-> Installing frontend dependencies (podman + Node 22 container)"
    podman run --rm -v "$PWD":/app:Z -w /app docker.io/library/node:22-alpine npm install
  fi
  echo "-> Starting frontend on http://localhost:${FRONTEND_PORT} (podman + Node 22 container)"
  # --network=host so the container's Vite proxy can reach the backend on localhost.
  podman run --rm --network=host \
    -e ECHO_BASE_BACKEND_HOST -e ECHO_BASE_BACKEND_PORT -e ECHO_BASE_ALLOWED_HOSTS \
    -v "$PWD":/app:Z -w /app \
    docker.io/library/node:22-alpine \
    npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
else
  echo "No npm or podman found -- install Node.js (see docs/INSTALL.md) or podman to run the frontend." >&2
  exit 1
fi

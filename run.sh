#!/usr/bin/env bash
# One-command launcher for Ops: migrates the DB, starts the FastAPI backend
# and the Vite frontend, opens the browser, and shuts both down on Ctrl+C.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/venv/bin"
BACKEND_PORT=8000
FRONTEND_PORT=5173
FRONTEND_URL="http://localhost:$FRONTEND_PORT"

PIDS=()
cleanup() {
  echo
  echo "Shutting down..."
  for pid in "${PIDS[@]:-}"; do
    [ -n "$pid" ] || continue
    pkill -TERM -P "$pid" 2>/dev/null || true   # children (vite under npm)
    kill -TERM "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# --- sanity checks -----------------------------------------------------------
if [ ! -x "$VENV/python" ]; then
  echo "venv not found at $ROOT/venv - create it with:"
  echo "  python3 -m venv venv && venv/bin/pip install -r code/requirements.txt"
  exit 1
fi
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Installing frontend dependencies (first run only)..."
  npm --prefix "$ROOT/frontend" install
fi
for port in $BACKEND_PORT $FRONTEND_PORT; do
  if lsof -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Port $port is already in use. Stop that process and re-run."
    exit 1
  fi
done

# --- database ----------------------------------------------------------------
echo "Applying database migrations..."
(cd "$ROOT/code" && "$VENV/alembic" upgrade head)

# --- backend -----------------------------------------------------------------
echo "Starting backend on :$BACKEND_PORT ..."
(cd "$ROOT/code" && exec "$VENV/uvicorn" app.main:app --port "$BACKEND_PORT") &
PIDS+=($!)

for _ in $(seq 1 40); do
  if curl -fs "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
if ! curl -fs "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
  echo "Backend failed to start."
  exit 1
fi
echo "Backend ready  ->  http://localhost:$BACKEND_PORT/docs"

# --- frontend ----------------------------------------------------------------
echo "Starting frontend on :$FRONTEND_PORT ..."
npm --prefix "$ROOT/frontend" run dev -- --port "$FRONTEND_PORT" --strictPort &
PIDS+=($!)

for _ in $(seq 1 40); do
  if curl -fs "$FRONTEND_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
echo "Frontend ready ->  $FRONTEND_URL"

if command -v open >/dev/null 2>&1; then
  open "$FRONTEND_URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$FRONTEND_URL"
fi

echo
echo "Ops is running. Press Ctrl+C to stop both servers."
# Exit (and clean up the other server) as soon as either one dies, instead of
# hanging with half the stack up. Polling keeps this working on macOS bash 3.2.
while :; do
  for pid in "${PIDS[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "A server process exited unexpectedly."
      exit 1
    fi
  done
  sleep 1
done

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
API_PORT="${API_PORT:-5000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_DB="${REDIS_DB:-2}"

declare -a STARTED_NAMES=()
declare -a STARTED_PIDS=()

log() {
  printf '[start] %s\n' "$*"
}

err() {
  printf '[start] ERROR: %s\n' "$*" >&2
}

cleanup() {
  for (( idx=${#STARTED_PIDS[@]}-1 ; idx>=0 ; idx-- )); do
    log "Stopping ${STARTED_NAMES[$idx]} (pid=${STARTED_PIDS[$idx]})..."
    kill "${STARTED_PIDS[$idx]}" 2>/dev/null || true
    wait "${STARTED_PIDS[$idx]}" 2>/dev/null || true
  done
  log "All services stopped"
}

trap cleanup INT TERM EXIT

# ── STEP 1: Dependencies ────────────────────────────────────────────

log "Installing backend dependencies (uv sync)..."
uv sync --directory "$BACKEND_DIR"

log "Installing frontend dependencies (pnpm install)..."
pnpm install --dir "$FRONTEND_DIR"

# ── STEP 2: Redis ───────────────────────────────────────────────────

start_redis() {
  if command -v redis-cli >/dev/null 2>&1 && redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
    log "Redis is already running on ${REDIS_HOST}:${REDIS_PORT}"
    return
  fi

  if command -v redis-server >/dev/null 2>&1; then
    log "Starting redis-server on ${REDIS_HOST}:${REDIS_PORT}..."
    redis-server --save "" --appendonly no --daemonize yes \
      --bind "$REDIS_HOST" --port "$REDIS_PORT"
    sleep 1
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
      log "redis-server started"
    else
      err "redis-server failed to start"
      exit 1
    fi
  else
    err "redis-server not found and Redis is not running"
    exit 1
  fi
}

start_redis

# ── STEP 3: Service check / start helpers ───────────────────────────

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :${port}" 2>/dev/null | awk 'NR>1 {print $4}' | grep -q ":${port}$" && return 0
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1 && return 0
  fi
  return 1
}

verify_started() {
  local pid="$1" name="$2"
  sleep 2
  if ! kill -0 "$pid" 2>/dev/null; then
    err "${name} exited during startup"
    exit 1
  fi
}

start_if_not_running() {
  local name="$1" port="$2"
  shift 2

  if port_in_use "$port"; then
    log "${name} is already running on port ${port}"
    return
  fi

  log "Starting ${name}..."
  "$@" &
  local pid=$!
  STARTED_NAMES+=("$name")
  STARTED_PIDS+=("$pid")
  verify_started "$pid" "$name"
  log "${name} started (pid=${pid})"
}

# ── STEP 4: Launch services ─────────────────────────────────────────

VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
CELERY_BIN="$BACKEND_DIR/.venv/bin/celery"

start_if_not_running "Flask API" "$API_PORT" \
  bash -c "cd '$BACKEND_DIR' && exec '$VENV_PYTHON' app.py"

CELERY_BROKER_URL="redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
export CELERY_BROKER_URL
export CELERY_RESULT_BACKEND="$CELERY_BROKER_URL"

start_if_not_running "Celery Worker" "" \
  bash -c "cd '$BACKEND_DIR' && exec '$CELERY_BIN' -A application.celery worker --loglevel=info --concurrency=4"

start_if_not_running "Celery Beat" "" \
  bash -c "cd '$BACKEND_DIR' && exec '$CELERY_BIN' -A application.celery beat --loglevel=info"

start_if_not_running "Frontend (Vite)" "$FRONTEND_PORT" \
  bash -lc "cd '$FRONTEND_DIR' && exec pnpm dev -- --strictPort --port ${FRONTEND_PORT}"

# ── STEP 5: Monitor ─────────────────────────────────────────────────

log "All services are up. Press Ctrl+C to stop everything."

while true; do
  sleep 2
  for pid in "${STARTED_PIDS[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      err "A service exited unexpectedly"
      exit 1
    fi
  done
done

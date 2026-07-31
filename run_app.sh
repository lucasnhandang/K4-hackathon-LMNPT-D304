#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/codebase/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
VENV_DIR="${ROOT_DIR}/.venv"

PYTHON_BIN="${PYTHON_BIN:-python3}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${PORT:-8080}"
BACKEND_URL="${BACKEND_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}/api/v1/chat}"

BACKEND_PID=""

log() {
  printf '[run_app] %s\n' "$*"
}

fail() {
  printf '[run_app] ERROR: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    log "Stopping backend (PID ${BACKEND_PID})..."
    kill "${BACKEND_PID}" 2>/dev/null || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
}

port_has_listener() {
  local port="$1"
  "${VENV_DIR}/bin/python" - "${port}" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.create_connection(("127.0.0.1", port), timeout=0.25):
    pass
PY
}

wait_for_backend() {
  local health_url="http://${BACKEND_HOST}:${BACKEND_PORT}/health"
  local attempt

  for attempt in {1..80}; do
    if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
      wait "${BACKEND_PID}" || true
      fail "Backend exited before becoming healthy."
    fi

    if "${VENV_DIR}/bin/python" - "${health_url}" <<'PY' 2>/dev/null
import json
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1], timeout=0.5) as response:
    payload = json.load(response)
    if response.status != 200 or payload.get("status") != "ok":
        raise SystemExit(1)
PY
    then
      log "Backend is healthy at ${health_url}"
      return 0
    fi

    sleep 0.25
  done

  fail "Backend did not become healthy within 20 seconds."
}

trap cleanup EXIT INT TERM

command -v "${PYTHON_BIN}" >/dev/null 2>&1 \
  || fail "Cannot find '${PYTHON_BIN}'. Install Python 3.9+ or set PYTHON_BIN."

[[ -f "${BACKEND_DIR}/requirements.txt" ]] \
  || fail "Missing ${BACKEND_DIR}/requirements.txt"
[[ -f "${FRONTEND_DIR}/requirements.txt" ]] \
  || fail "Missing ${FRONTEND_DIR}/requirements.txt"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  log "Creating virtual environment at ${VENV_DIR}..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

log "Installing backend and frontend requirements..."
"${VENV_DIR}/bin/python" -m pip install \
  -r "${BACKEND_DIR}/requirements.txt" \
  -r "${FRONTEND_DIR}/requirements.txt"

if port_has_listener "${BACKEND_PORT}" 2>/dev/null; then
  fail "Port ${BACKEND_PORT} is already in use. Set BACKEND_PORT to another port."
fi
if port_has_listener "${FRONTEND_PORT}" 2>/dev/null; then
  fail "Port ${FRONTEND_PORT} is already in use. Set PORT to another port."
fi

log "Starting backend at http://${BACKEND_HOST}:${BACKEND_PORT}..."
(
  cd "${BACKEND_DIR}"
  backend_command=(
    "${VENV_DIR}/bin/python" -m uvicorn server:app
    --host "${BACKEND_HOST}"
    --port "${BACKEND_PORT}"
  )
  if [[ -f "${BACKEND_DIR}/.env" ]]; then
    backend_command+=(--env-file "${BACKEND_DIR}/.env")
  fi
  exec "${backend_command[@]}"
) &
BACKEND_PID=$!

wait_for_backend

log "Starting frontend at http://127.0.0.1:${FRONTEND_PORT}"
log "Frontend will call ${BACKEND_URL}"
log "Press Ctrl+C to stop both services."

cd "${FRONTEND_DIR}"
PORT="${FRONTEND_PORT}" \
BACKEND_URL="${BACKEND_URL}" \
USE_LOCAL_MOCK="false" \
"${VENV_DIR}/bin/python" main.py

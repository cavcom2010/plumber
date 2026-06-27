#!/usr/bin/env bash
# preflight.sh — Shared Django deploy preflight checks.
# Source this from deploy scripts. Expects ROOT and PYTHON_BIN to be set;
# falls back to resolving them relative to this script's location.

set -euo pipefail

if [[ -z "${ROOT:-}" ]]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

PYTHON_BIN="${PYTHON_BIN:-$ROOT/venv/bin/python}"

RUN_MANAGE_CHECK="${RUN_MANAGE_CHECK:-1}"
CHECK_MODEL_MIGRATIONS="${CHECK_MODEL_MIGRATIONS:-1}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
COLLECTSTATIC="${COLLECTSTATIC:-1}"

run_manage_command() {
  local label="$1"
  shift

  echo "${label}..."
  "$PYTHON_BIN" manage.py "$@"
}

echo "Running Django preflight checks..."

if [[ "$RUN_MANAGE_CHECK" == "1" ]]; then
  run_manage_command "Running python manage.py check" check
fi

if [[ "$CHECK_MODEL_MIGRATIONS" == "1" ]]; then
  run_manage_command "Checking for missing migration files" makemigrations --check --dry-run
fi

if [[ "$RUN_MIGRATIONS" == "1" ]]; then
  if "$PYTHON_BIN" manage.py migrate --check --noinput >/dev/null 2>&1; then
    echo "Database migrations are already applied."
  else
    run_manage_command "Applying database migrations" migrate --noinput
  fi
fi

echo "Ensuring cache table exists..."
"$PYTHON_BIN" manage.py createcachetable >/dev/null 2>&1 || true

if [[ "$COLLECTSTATIC" == "1" ]]; then
  echo "Collecting static files..."
  "$PYTHON_BIN" manage.py collectstatic --noinput >/dev/null
fi

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="$ROOT/venv/bin/python"
GUNICORN_BIN="$ROOT/venv/bin/gunicorn"

print_usage() {
  cat <<'EOF'
Usage: ./deploy/home/start.sh [--foreground|--daemon] [--help]

Options:
  --foreground  Keep Gunicorn attached to this terminal and stream logs live (default).
  --daemon      Run Gunicorn detached in the background.
  --help        Show this help text.

Environment:
  HOME_FOREGROUND=1       Same as --foreground (default).
  HOME_FOREGROUND=0       Same as --daemon.
  HOME_PORT=8021          Preferred public Nginx port. If busy, the next free port up is used.
  HOME_APP_PORT=9021      Preferred internal Gunicorn port. If busy, the next free port up is used.
  HOME_BIND=0.0.0.0       Nginx bind address.
  HOME_APP_MODULE=flowpro.wsgi:application
  HOME_COLLECTSTATIC=1    Run collectstatic before start.
  HOME_RUN_MIGRATIONS=1   Apply pending migrations before start.
EOF
}

if [[ ! -x "$PYTHON_BIN" ]] || [[ ! -x "$GUNICORN_BIN" ]]; then
  echo "Missing venv binaries at $ROOT/venv. Run: source venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

case "${HOME_FOREGROUND:-1}" in
  1|true|TRUE|yes|YES|on|ON)
    HOME_FOREGROUND_MODE=1
    ;;
  0|false|FALSE|no|NO|off|OFF|"")
    HOME_FOREGROUND_MODE=0
    ;;
  *)
    echo "Invalid HOME_FOREGROUND value: ${HOME_FOREGROUND}" >&2
    exit 1
    ;;
esac

while [[ $# -gt 0 ]]; do
  case "$1" in
    --foreground)
      HOME_FOREGROUND_MODE=1
      ;;
    --daemon)
      HOME_FOREGROUND_MODE=0
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      print_usage >&2
      exit 1
      ;;
  esac
  shift
done

export DJANGO_SETTINGS_MODULE="${HOME_DJANGO_SETTINGS_MODULE:-${DJANGO_SETTINGS_MODULE:-flowpro.settings}}"

HOME_DIR="$ROOT/.home_nginx"
LOG_DIR="$HOME_DIR/logs"
RUN_DIR="$HOME_DIR/run"
TMP_DIR="$HOME_DIR/tmp"

mkdir -p "$LOG_DIR" "$RUN_DIR"
mkdir -p "$TMP_DIR/client_body" "$TMP_DIR/proxy" "$TMP_DIR/fastcgi" "$TMP_DIR/uwsgi" "$TMP_DIR/scgi"

detect_lan_ip() {
  local ip=""

  if [[ -n "${HOME_INTERFACE:-}" ]]; then
    ip="$(ip -o -4 addr show dev "${HOME_INTERFACE}" scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -n1 || true)"
  fi

  if [[ -z "$ip" ]]; then
    ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1; i<=NF; i++) if ($i=="src") {print $(i+1); exit}}' || true)"
  fi

  if [[ -z "$ip" ]]; then
    ip="$(hostname -I 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i !~ /^127\./) {print $i; exit}}' || true)"
  fi

  if [[ -z "$ip" ]]; then
    ip="127.0.0.1"
  fi

  printf '%s' "$ip"
}

normalize_csv_unique() {
  local raw="$1"
  local out=""
  local token=""
  declare -A seen=()
  IFS=',' read -ra parts <<< "$raw"
  for token in "${parts[@]}"; do
    token="${token#"${token%%[![:space:]]*}"}"
    token="${token%"${token##*[![:space:]]}"}"
    [[ -z "$token" ]] && continue
    if [[ -z "${seen[$token]+x}" ]]; then
      seen["$token"]=1
      if [[ -z "$out" ]]; then
        out="$token"
      else
        out="${out},${token}"
      fi
    fi
  done
  printf '%s' "$out"
}

port_in_use() {
  ss -ltn "sport = :$1" | awk 'NR>1 {print $4}' | grep -q ":$1$"
}

first_free_port() {
  local port="$1"
  while port_in_use "$port"; do
    port=$((port + 1))
  done
  printf '%s' "$port"
}

wait_for_port() {
  local port="$1"

  for _ in {1..50}; do
    if port_in_use "$port"; then
      return 0
    fi
    sleep 0.2
  done

  return 1
}

read_pid_file() {
  local pid_file="$1"
  local pid=""

  [[ -f "$pid_file" ]] || return 1
  pid="$(tr -dc '0-9' < "$pid_file")"
  [[ -n "$pid" ]] || return 1

  printf '%s' "$pid"
}

pid_is_running() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

kill_pid_tree() {
  local pid="$1"
  local child_pids=""
  child_pids="$(pgrep -P "$pid" || true)"

  kill -TERM "$pid" 2>/dev/null || true
  if [[ -n "$child_pids" ]]; then
    kill -TERM $child_pids 2>/dev/null || true
  fi

  for _ in {1..25}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.2
  done

  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL "$pid" 2>/dev/null || true
  fi
}

start_log_stream() {
  local label="$1"
  local logfile="$2"
  local pid_var="$3"

  touch "$logfile"
  (
    tail -n0 -F "$logfile" 2>/dev/null | sed -u "s/^/[${label}] /"
  ) &
  printf -v "$pid_var" '%s' "$!"
}

LAN_IP="${HOME_HOST:-$(detect_lan_ip)}"
HOME_BIND="${HOME_BIND:-0.0.0.0}"
PREFERRED_NGINX_PORT="${HOME_PORT:-8021}"
PREFERRED_GUNICORN_PORT="${HOME_APP_PORT:-9021}"
GUNICORN_WORKERS="${HOME_GUNICORN_WORKERS:-3}"
GUNICORN_TIMEOUT="${HOME_GUNICORN_TIMEOUT:-120}"
APP_MODULE="${HOME_APP_MODULE:-${GUNICORN_APP_MODULE:-flowpro.wsgi:application}}"
COLLECTSTATIC="${HOME_COLLECTSTATIC:-1}"
RUN_MANAGE_CHECK="${HOME_RUN_MANAGE_CHECK:-1}"
CHECK_MODEL_MIGRATIONS="${HOME_CHECK_MODEL_MIGRATIONS:-1}"
RUN_MIGRATIONS="${HOME_RUN_MIGRATIONS:-1}"

GUNICORN_PID="$RUN_DIR/gunicorn.pid"
NGINX_PID="$RUN_DIR/nginx.pid"
HOME_HOST_FILE="$RUN_DIR/home_host"
HOME_SCHEME_FILE="$RUN_DIR/home_scheme"
HOME_PORT_FILE="$RUN_DIR/home_port"
FOREGROUND_GUNICORN_PID=""
FOREGROUND_NGINX_ACCESS_LOG_PID=""
FOREGROUND_NGINX_ERROR_LOG_PID=""
FOREGROUND_CLEANED_UP=0

stop_foreground_services() {
  [[ "$FOREGROUND_CLEANED_UP" == "1" ]] && return
  FOREGROUND_CLEANED_UP=1

  if [[ -n "$FOREGROUND_NGINX_ACCESS_LOG_PID" ]] && kill -0 "$FOREGROUND_NGINX_ACCESS_LOG_PID" 2>/dev/null; then
    kill_pid_tree "$FOREGROUND_NGINX_ACCESS_LOG_PID"
  fi

  if [[ -n "$FOREGROUND_NGINX_ERROR_LOG_PID" ]] && kill -0 "$FOREGROUND_NGINX_ERROR_LOG_PID" 2>/dev/null; then
    kill_pid_tree "$FOREGROUND_NGINX_ERROR_LOG_PID"
  fi

  if [[ -n "$FOREGROUND_GUNICORN_PID" ]] && kill -0 "$FOREGROUND_GUNICORN_PID" 2>/dev/null; then
    echo
    echo "Stopping foreground Gunicorn (pid ${FOREGROUND_GUNICORN_PID})..."
    kill_pid_tree "$FOREGROUND_GUNICORN_PID"
  fi
  rm -f "$GUNICORN_PID"

  if [[ -f "$NGINX_PID" ]]; then
    echo "Stopping Nginx..."
    nginx -p "$HOME_DIR" -c "$HOME_DIR/nginx.conf" -s stop 2>/dev/null || true
    rm -f "$NGINX_PID"
  fi

  rm -f "$HOME_HOST_FILE" "$HOME_SCHEME_FILE" "$HOME_PORT_FILE"
}

trap 'stop_foreground_services' EXIT
trap 'trap - EXIT INT TERM; stop_foreground_services; exit 130' INT
trap 'trap - EXIT INT TERM; stop_foreground_services; exit 143' TERM

if [[ -f "$NGINX_PID" ]] && pid_is_running "$(cat "$NGINX_PID")"; then
  echo "Stopping existing home Nginx (pid $(cat "$NGINX_PID"))..."
  nginx -p "$HOME_DIR" -c "$HOME_DIR/nginx.conf" -s stop 2>/dev/null || true
  rm -f "$NGINX_PID"
fi

if [[ -f "$GUNICORN_PID" ]] && pid_is_running "$(cat "$GUNICORN_PID")"; then
  echo "Stopping existing home Gunicorn (pid $(cat "$GUNICORN_PID"))..."
  kill_pid_tree "$(cat "$GUNICORN_PID")"
  rm -f "$GUNICORN_PID"
fi

NGINX_PORT="$(first_free_port "$PREFERRED_NGINX_PORT")"
GUNICORN_PORT="$(first_free_port "$PREFERRED_GUNICORN_PORT")"

if [[ "$NGINX_PORT" != "$PREFERRED_NGINX_PORT" ]]; then
  echo "Port ${PREFERRED_NGINX_PORT} is busy; using next free public port ${NGINX_PORT}."
fi

if [[ "$GUNICORN_PORT" != "$PREFERRED_GUNICORN_PORT" ]]; then
  echo "Internal app port ${PREFERRED_GUNICORN_PORT} is busy; using ${GUNICORN_PORT}."
fi

# Keep home/LAN mode HTTP-first.
export SECURE_SSL_REDIRECT="${HOME_SECURE_SSL_REDIRECT:-false}"
export SESSION_COOKIE_SECURE="${HOME_SESSION_COOKIE_SECURE:-false}"
export CSRF_COOKIE_SECURE="${HOME_CSRF_COOKIE_SECURE:-false}"
export SECURE_HSTS_SECONDS="${HOME_SECURE_HSTS_SECONDS:-0}"
export USE_X_FORWARDED_HOST="${HOME_USE_X_FORWARDED_HOST:-false}"
export USE_X_FORWARDED_PORT="${HOME_USE_X_FORWARDED_PORT:-false}"

ALLOWED_BASE="${ALLOWED_HOSTS:-localhost,127.0.0.1}"
CSRF_BASE="${CSRF_TRUSTED_ORIGINS:-http://localhost,http://127.0.0.1}"
LOCAL_ORIGINS="http://localhost:${NGINX_PORT},http://127.0.0.1:${NGINX_PORT}"

export ALLOWED_HOSTS="$(normalize_csv_unique "${ALLOWED_BASE},${LAN_IP}")"
export CSRF_TRUSTED_ORIGINS="$(normalize_csv_unique "${CSRF_BASE},${LOCAL_ORIGINS},http://${LAN_IP}:${NGINX_PORT}")"
export SITE_PROTO="http"
export SITE_DOMAIN="${LAN_IP}:${NGINX_PORT}"

run_manage_command() {
  local label="$1"
  shift

  echo "${label}..."
  "$PYTHON_BIN" manage.py "$@"
}

echo "Running Django preflight before starting services..."
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

if [[ "$COLLECTSTATIC" == "1" ]]; then
  echo "Collecting static files..."
  "$PYTHON_BIN" manage.py collectstatic --noinput >/dev/null
fi

if [[ "$HOME_FOREGROUND_MODE" == "1" ]]; then
  echo "Starting Gunicorn on 127.0.0.1:${GUNICORN_PORT} in foreground mode..."
  "$GUNICORN_BIN" \
    "$APP_MODULE" \
    --bind "127.0.0.1:${GUNICORN_PORT}" \
    --workers "$GUNICORN_WORKERS" \
    --timeout "$GUNICORN_TIMEOUT" \
    --access-logfile "-" \
    --error-logfile "-" \
    --capture-output \
    --log-level info \
    --pid "$GUNICORN_PID" &
  FOREGROUND_GUNICORN_PID="$!"

  if ! wait_for_port "$GUNICORN_PORT"; then
    echo "Gunicorn did not start listening on 127.0.0.1:${GUNICORN_PORT}." >&2
    exit 1
  fi
else
  echo "Starting Gunicorn on 127.0.0.1:${GUNICORN_PORT}..."
  "$GUNICORN_BIN" \
    "$APP_MODULE" \
    --bind "127.0.0.1:${GUNICORN_PORT}" \
    --workers "$GUNICORN_WORKERS" \
    --timeout "$GUNICORN_TIMEOUT" \
    --access-logfile "$LOG_DIR/gunicorn-access.log" \
    --error-logfile "$LOG_DIR/gunicorn-error.log" \
    --capture-output \
    --log-level info \
    --daemon \
    --pid "$GUNICORN_PID"

  if ! wait_for_port "$GUNICORN_PORT"; then
    echo "Gunicorn did not start listening on 127.0.0.1:${GUNICORN_PORT}." >&2
    exit 1
  fi
fi

STATIC_ROOT="$ROOT/staticfiles"
MEDIA_ROOT="$ROOT/media"
NGINX_CONF="$HOME_DIR/nginx.conf"

cat >"$NGINX_CONF" <<EOF_NGINX
worker_processes  1;
pid run/nginx.pid;

events {
  worker_connections  1024;
}

http {
  include       /etc/nginx/mime.types;
  default_type  application/octet-stream;

  access_log  logs/access.log;
  error_log   logs/error.log info;
  sendfile    on;
  keepalive_timeout  65;

  client_body_temp_path tmp/client_body;
  proxy_temp_path tmp/proxy;
  fastcgi_temp_path tmp/fastcgi;
  uwsgi_temp_path tmp/uwsgi;
  scgi_temp_path tmp/scgi;

  upstream plumber_app {
    server 127.0.0.1:${GUNICORN_PORT};
    keepalive 16;
  }

  server {
    listen ${HOME_BIND}:${NGINX_PORT};
    server_name _;

    client_max_body_size 25m;

    location /static/ {
      alias ${STATIC_ROOT}/;
      expires 7d;
      add_header Cache-Control "public, max-age=604800";
    }

    location /media/ {
      alias ${MEDIA_ROOT}/;
      expires 7d;
      add_header Cache-Control "public, max-age=604800";
    }

    location / {
      proxy_pass http://plumber_app;
      proxy_set_header Host \$http_host;
      proxy_set_header X-Real-IP \$remote_addr;
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto \$scheme;
      proxy_redirect off;
      proxy_read_timeout ${GUNICORN_TIMEOUT};
      proxy_send_timeout ${GUNICORN_TIMEOUT};
    }
  }
}
EOF_NGINX

echo "Starting Nginx on ${HOME_BIND}:${NGINX_PORT}..."
nginx -p "$HOME_DIR" -c "$NGINX_CONF"

if [[ "$HOME_FOREGROUND_MODE" == "1" ]]; then
  start_log_stream "nginx:error" "$LOG_DIR/error.log" FOREGROUND_NGINX_ERROR_LOG_PID
  start_log_stream "nginx:access" "$LOG_DIR/access.log" FOREGROUND_NGINX_ACCESS_LOG_PID
fi

printf '%s' "$LAN_IP" >"$HOME_HOST_FILE"
printf 'http' >"$HOME_SCHEME_FILE"
printf '%s' "$NGINX_PORT" >"$HOME_PORT_FILE"

if command -v curl >/dev/null 2>&1; then
  HEALTHCHECK_HOST="127.0.0.1"
  if [[ "$HOME_BIND" != "0.0.0.0" && "$HOME_BIND" != "::" ]]; then
    HEALTHCHECK_HOST="$HOME_BIND"
  fi

  HEALTHCHECK_OK=0
  for _ in {1..20}; do
    if curl -fsS --max-time 5 "http://${HEALTHCHECK_HOST}:${NGINX_PORT}/" >/dev/null; then
      HEALTHCHECK_OK=1
      break
    fi
    sleep 0.3
  done

  if [[ "$HEALTHCHECK_OK" != "1" ]]; then
    echo "HTTP health check failed on ${HEALTHCHECK_HOST}:${NGINX_PORT}." >&2
    echo "Check .home_nginx/logs/error.log and .home_nginx/logs/gunicorn-error.log" >&2
    exit 1
  fi
fi

echo "Done."
echo "Open local: http://127.0.0.1:${NGINX_PORT}/"
echo "Open: http://${LAN_IP}:${NGINX_PORT}/"

if [[ "$HOME_FOREGROUND_MODE" == "1" ]]; then
  echo "Foreground mode active. Press Ctrl+C to stop Gunicorn and Nginx."
  set +e
  wait "$FOREGROUND_GUNICORN_PID"
  GUNICORN_EXIT_CODE="$?"
  set -e
  trap - EXIT INT TERM
  stop_foreground_services
  exit "$GUNICORN_EXIT_CODE"
fi

trap - EXIT INT TERM

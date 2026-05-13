#!/bin/sh
set -eu

DB_NAME="${DB_NAME:-sports_portal}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
EXTERNAL_DB_HOST="${DB_HOST:-192.168.0.50}"
EXTERNAL_DB_PORT="${DB_PORT:-5434}"
EXTERNAL_REDIS_URL="${REDIS_URL:-redis://192.168.0.50:6379/0}"

redis_host() {
  python3 -c 'import sys; from urllib.parse import urlparse; print(urlparse(sys.argv[1]).hostname or "")' "${EXTERNAL_REDIS_URL}"
}

redis_port() {
  python3 -c 'import sys; from urllib.parse import urlparse; print(urlparse(sys.argv[1]).port or 6379)' "${EXTERNAL_REDIS_URL}"
}

postgres_ready() {
  host="$1"
  port="$2"

  nc -z "${host}" "${port}" >/dev/null 2>&1 || return 1

  if command -v psql >/dev/null 2>&1; then
    PGPASSWORD="${DB_PASSWORD}" psql \
      -h "${host}" \
      -p "${port}" \
      -U "${DB_USER}" \
      -d postgres \
      -tAc "SELECT 1" >/dev/null 2>&1
    return $?
  fi

  return 0
}

write_runtime_env() {
  cat > .env.runtime <<EOF
DEBUG=${DJANGO_DEBUG:-1}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${1}
DB_PORT=${2}
REDIS_URL=${3}
WEB_PORT=${WEB_PORT:-8002}
EOF
}

compose() {
  docker compose --env-file .env.runtime "$@"
}

fallback_services=""

if postgres_ready "${EXTERNAL_DB_HOST}" "${EXTERNAL_DB_PORT}"; then
  DB_HOST_RUNTIME="${EXTERNAL_DB_HOST}"
  DB_PORT_RUNTIME="${EXTERNAL_DB_PORT}"
  echo "Using existing Postgres at ${DB_HOST_RUNTIME}:${DB_PORT_RUNTIME}"
else
  DB_HOST_RUNTIME="postgres"
  DB_PORT_RUNTIME="5432"
  fallback_services="${fallback_services} postgres"
  echo "Existing Postgres is not reachable; using local compose Postgres."
fi

REDIS_HOST="$(redis_host)"
REDIS_PORT="$(redis_port)"
if [ -n "${REDIS_HOST}" ] && nc -z "${REDIS_HOST}" "${REDIS_PORT}" >/dev/null 2>&1; then
  REDIS_URL_RUNTIME="${EXTERNAL_REDIS_URL}"
  echo "Using existing Redis at ${REDIS_HOST}:${REDIS_PORT}"
else
  REDIS_URL_RUNTIME="redis://redis:6379/0"
  fallback_services="${fallback_services} redis"
  echo "Existing Redis is not reachable; using local compose Redis."
fi

write_runtime_env "${DB_HOST_RUNTIME}" "${DB_PORT_RUNTIME}" "${REDIS_URL_RUNTIME}"

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "DRY_RUN=1 set; wrote .env.runtime and did not start containers."
  exit 0
fi

if [ -n "${fallback_services}" ]; then
  compose --profile local-deps up -d ${fallback_services}
fi

compose --profile tools run --rm db-init
compose up -d --build web celery celery-beat

echo "Sports portal is starting on http://localhost:${WEB_PORT:-8002}"

#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-web}"

wait_for_pg() {
  if [[ -n "${POSTGRES_HOST:-}" && -n "${POSTGRES_USER:-}" ]]; then
    echo "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
    until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" >/dev/null 2>&1; do
      sleep 1
    done
    echo "Postgres is ready."
  fi
}

if [[ "$ROLE" == "web" ]]; then
  wait_for_pg
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput || true
  exec gunicorn mixtum_core.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout ${GUNICORN_TIMEOUT:-120}
elif [[ "$ROLE" == "dev" ]]; then
  wait_for_pg
  python manage.py migrate --noinput
  exec python manage.py runserver 0.0.0.0:8000
elif [[ "$ROLE" == "worker" ]]; then
  wait_for_pg
  exec celery -A mixtum_core worker -l ${CELERY_LOG_LEVEL:-info}
elif [[ "$ROLE" == "beat" ]]; then
  wait_for_pg
  exec celery -A mixtum_core beat -l ${CELERY_LOG_LEVEL:-info} --scheduler django_celery_beat.schedulers:DatabaseScheduler
fi

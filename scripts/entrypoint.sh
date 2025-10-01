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

has_module() {
  python - <<'PY'
import importlib, sys
mod = sys.argv[1]
try:
    importlib.import_module(mod)
    print("YES")
except Exception:
    print("NO")
PY
}

wait_for_pg

case "$ROLE" in
  web)
    python manage.py migrate --noinput
    # In prod/stage può servirti:
    python manage.py collectstatic --noinput || true
    exec gunicorn mixtum_core.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers ${GUNICORN_WORKERS:-3} \
      --timeout ${GUNICORN_TIMEOUT:-120}
    ;;

  dev)
    # Sviluppo: autoreload affidabile anche su bind mount (Docker Desktop)
    python manage.py migrate --noinput
    if [[ "$(has_module watchdog)" == "YES" ]]; then
      echo "Running DEV with watchdog auto-restart"
      exec python -m watchdog.cli.watchmedo auto-restart \
        --directory=/app \
        --recursive \
        --pattern="*.py;*.html;*.jinja;*.jinja2;*.tmpl;*.txt" \
        -- \
        python manage.py runserver 0.0.0.0:8000
    else
      echo "Running DEV with Django autoreloader"
      exec python manage.py runserver 0.0.0.0:8000
    fi
    ;;

  worker)
    # Celery worker con autoreload se supportato (>=5.2). In alternativa, watchdog.
    if celery --help 2>/dev/null | grep -q -- "--autoreload"; then
      echo "Starting Celery worker with --autoreload"
      # --pool=solo consigliato con autoreload
      exec celery -A mixtum_core worker --loglevel=${CELERY_LOG_LEVEL:-INFO} --pool=solo --autoreload
    elif [[ "$(has_module watchdog)" == "YES" ]]; then
      echo "Starting Celery worker wrapped by watchdog auto-restart"
      exec python -m watchdog.cli.watchmedo auto-restart \
        --directory=/app \
        --recursive \
        --pattern="*.py" \
        -- \
        celery -A mixtum_core worker --loglevel=${CELERY_LOG_LEVEL:-INFO} --pool=solo
    else
      exec celery -A mixtum_core worker --loglevel=${CELERY_LOG_LEVEL:-INFO}
    fi
    ;;

  beat)
    # Celery beat: nessun autoreload nativo; wrapper watchdog se vuoi anche qui
    if [[ "$(has_module watchdog)" == "YES" ]]; then
      echo "Starting Celery beat wrapped by watchdog auto-restart"
      exec python -m watchdog.cli.watchmedo auto-restart \
        --directory=/app \
        --recursive \
        --pattern="*.py" \
        -- \
        celery -A mixtum_core beat --loglevel=${CELERY_LOG_LEVEL:-INFO} --scheduler django_celery_beat.schedulers:DatabaseScheduler
    else
      exec celery -A mixtum_core beat --loglevel=${CELERY_LOG_LEVEL:-INFO} --scheduler django_celery_beat.schedulers:DatabaseScheduler
    fi
    ;;

  *)
    exec "$ROLE" "${@:2}"
    ;;
esac

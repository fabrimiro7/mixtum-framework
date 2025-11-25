#!/usr/bin/env bash
set -euo pipefail

# =========================
# Config / helpers
# =========================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COMPOSE_BASE="${ROOT_DIR}/docker-compose.yml"
COMPOSE_PROD="${ROOT_DIR}/docker-compose.prod.yml"
ENV_FILE="${ROOT_DIR}/.env"

log() { echo -e "✅ $*"; }
warn() { echo -e "⚠️  $*" >&2; }
err() { echo -e "❌ $*" >&2; }

require_file() {
  local f="$1"
  if [[ ! -f "$f" ]]; then
    err "Missing required file: $f"
    exit 1
  fi
}

compose() {
  docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_PROD" "$@"
}

# Naive .env loader (works for simple KEY=VALUE lines)
load_env() {
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
}

# =========================
# Pre-flight checks
# =========================

cd "$ROOT_DIR"

require_file "$COMPOSE_BASE"
require_file "$COMPOSE_PROD"
require_file "$ENV_FILE"
require_file "$ROOT_DIR/nginx/init.sh"
require_file "$ROOT_DIR/nginx/ssl-watch.sh"
require_file "$ROOT_DIR/certbot/entrypoint.sh"

load_env

: "${SERVER_NAME:?SERVER_NAME missing in .env}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL missing in .env}"

# =========================
# Permissions
# =========================

log "Setting executable permissions..."
chmod +x "$ROOT_DIR/nginx/init.sh" \
         "$ROOT_DIR/nginx/ssl-watch.sh" \
         "$ROOT_DIR/certbot/entrypoint.sh" \
         "$ROOT_DIR/scripts/entrypoint.sh" || true

# Ensure certbot storage exists
mkdir -p "$ROOT_DIR/letsencrypt_data" "$ROOT_DIR/certbot-www"

# =========================
# Deploy
# =========================

log "Building and starting stack (PROD)..."
compose up -d --build

log "Waiting for Nginx to be reachable on port 80..."
# We wait up to ~60s, no hard dependency on curl success (some envs block localhost checks)
for i in {1..30}; do
  if curl -fsS "http://127.0.0.1/.well-known/acme-challenge/ping" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

log "Triggering first certificate issuance (if missing)..."
# This will do nothing if cert already exists; it runs in addition to the certbot loop.
# Useful for deterministic "first deploy" results.
compose run --rm certbot /bin/sh -c '
  set -eu
  : "${SERVER_NAME:?}"
  : "${CERTBOT_EMAIL:?}"
  CERT_PATH="/etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem"
  if [ -f "$CERT_PATH" ]; then
    echo "[deploy] Certificate already present, skipping initial issuance."
    exit 0
  fi
  echo "[deploy] Issuing certificate for ${SERVER_NAME}..."
  certbot certonly --webroot -w /var/www/certbot -d "${SERVER_NAME}" \
    --email "${CERTBOT_EMAIL}" --agree-tos --non-interactive --rsa-key-size 4096
  touch /var/www/certbot/.nginx-reload
'

log "Restarting Nginx to ensure it picks up HTTPS (safe even if watcher already did)..."
compose exec -T nginx nginx -t
compose exec -T nginx nginx -s reload || true

log "Stack status:"
compose ps

log "Deployment complete!"
echo "   👉 https://${SERVER_NAME}"

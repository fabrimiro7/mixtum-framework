#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COMPOSE_BASE="${ROOT_DIR}/docker-compose.yml"
COMPOSE_PROD="${ROOT_DIR}/docker-compose.prod.yml"
ENV_FILE="${ROOT_DIR}/.env"
PROFILE="${DEPLOY_PROFILE:-backend}"
NGINX_SERVICE="nginx"

log() { echo -e "✅ $*"; }
warn(){ echo -e "⚠️  $*" >&2; }
err() { echo -e "❌ $*" >&2; }

compose() {
  docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_PROD" --profile "$PROFILE" "$@"
}

require_file() {
  [[ -f "$1" ]] || { err "Missing file: $1"; exit 1; }
}

load_env() {
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

cd "$ROOT_DIR"

require_file "$COMPOSE_BASE"
require_file "$COMPOSE_PROD"
require_file "$ENV_FILE"
require_file "$ROOT_DIR/nginx/init.sh"
require_file "$ROOT_DIR/nginx/ssl-watch.sh"
require_file "$ROOT_DIR/certbot/entrypoint.sh"
require_file "$ROOT_DIR/scripts/entrypoint.sh"

load_env
: "${SERVER_NAME:?SERVER_NAME missing in .env}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL missing in .env}"

if [[ "$PROFILE" == "frontend" ]]; then
  NGINX_SERVICE="nginx_frontend"
fi

log "Setting executable permissions..."
chmod +x \
  "$ROOT_DIR/nginx/init.sh" \
  "$ROOT_DIR/nginx/ssl-watch.sh" \
  "$ROOT_DIR/certbot/entrypoint.sh" \
  "$ROOT_DIR/scripts/entrypoint.sh" || true

mkdir -p "$ROOT_DIR/letsencrypt_data" "$ROOT_DIR/certbot-www"

CERT_PATH_HOST="$ROOT_DIR/letsencrypt_data/live/${SERVER_NAME}/fullchain.pem"
RENEW_CONF_HOST="$ROOT_DIR/letsencrypt_data/renewal/${SERVER_NAME}.conf"

log "Building and starting stack (PROD, profile: ${PROFILE})..."
compose up -d --build

log "Waiting for Nginx on port 80 (best-effort)..."
for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1/.well-known/acme-challenge/ping" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

# --- Renewal config sanity (host-side) ---
if [[ -f "$RENEW_CONF_HOST" ]]; then
  # Cheap sanity check: must contain cert/key/chain file references
  if ! grep -qE '^(cert|privkey|chain|fullchain)\s*=' "$RENEW_CONF_HOST"; then
    warn "Renewal config looks broken: $RENEW_CONF_HOST"
    cp "$RENEW_CONF_HOST" "${RENEW_CONF_HOST}.bak.$(date +%Y%m%d_%H%M%S)" || true
    mv "$RENEW_CONF_HOST" "${RENEW_CONF_HOST}.broken.$(date +%Y%m%d_%H%M%S)" || true
    warn "Moved broken renewal config aside so it can be regenerated."
  fi
fi

# --- Issue / repair cert (one-shot with explicit entrypoint) ---
log "Ensuring certificate exists and renewal config is valid..."
compose run --rm --entrypoint certbot certbot \
  certonly --webroot -w /var/www/certbot \
  -d "${SERVER_NAME}" \
  --email "${CERTBOT_EMAIL}" \
  --agree-tos --non-interactive \
  --rsa-key-size 4096 \
  --keep-until-expiring

# Signal nginx reload (watcher will also pick this up)
touch "$ROOT_DIR/certbot-www/.nginx-reload" || true

log "Reloading Nginx (safe)..."
compose exec -T "$NGINX_SERVICE" nginx -t
compose exec -T "$NGINX_SERVICE" nginx -s reload || true

log "Starting certbot service (renew loop)..."
compose up -d certbot

log "Quick dry-run renew test..."
set +e
compose run --rm --entrypoint certbot certbot renew --dry-run --webroot -w /var/www/certbot
DRY_RUN_RC=$?
set -e
if [[ $DRY_RUN_RC -ne 0 ]]; then
  warn "Dry-run renew failed. Check certbot logs:"
  warn "  docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=200 certbot"
else
  log "Dry-run renew OK."
fi

log "Stack status:"
compose ps

log "Deployment complete! 👉 https://${SERVER_NAME}"

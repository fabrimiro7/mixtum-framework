#!/bin/sh
set -eu

: "${SERVER_NAME:?SERVER_NAME missing}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL missing}"

WEBROOT="/var/www/certbot"
CERT_PATH="/etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem"
RSA_KEY_SIZE="${RSA_KEY_SIZE:-4096}"
STAGING="${CERTBOT_STAGING:-0}"

mkdir -p "$WEBROOT"

# Give nginx a moment to start
sleep 3

if [ ! -f "$CERT_PATH" ]; then
  echo "[certbot] Requesting first certificate for ${SERVER_NAME}..."
  staging_flag=""
  if [ "$STAGING" = "1" ]; then staging_flag="--staging"; fi

  certbot certonly --webroot -w "$WEBROOT" -d "$SERVER_NAME" \
    --email "$CERTBOT_EMAIL" --agree-tos --non-interactive \
    --rsa-key-size "$RSA_KEY_SIZE" $staging_flag

  echo "[certbot] First certificate obtained."
  touch "$WEBROOT/.nginx-reload"
else
  echo "[certbot] Certificate already present."
fi

echo "[certbot] Starting renew loop..."
while :; do
  certbot renew --webroot -w "$WEBROOT" --quiet \
    --deploy-hook "touch $WEBROOT/.nginx-reload"
  sleep 12h
done

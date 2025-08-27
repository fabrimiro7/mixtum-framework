#!/bin/sh
set -eu

: "${SERVER_NAME:?SERVER_NAME is required}"

envsubst '$SERVER_NAME' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

LIVE_DIR="/etc/letsencrypt/live/${SERVER_NAME}"
FULL="${LIVE_DIR}/fullchain.pem"
PRIV="${LIVE_DIR}/privkey.pem"

if [ ! -f "$FULL" ] || [ ! -f "$PRIV" ]; then
  echo "Generating dummy SSL certificate for ${SERVER_NAME}..."
  mkdir -p "$LIVE_DIR"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$PRIV" -out "$FULL" -subj "/CN=${SERVER_NAME}" >/dev/null 2>&1
  echo "Dummy certificate generated."
fi
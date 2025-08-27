#!/bin/sh
set -eu

: "${SERVER_NAME:?SERVER_NAME is required}"

LIVE_DIR="/etc/letsencrypt/live/${SERVER_NAME}"
ARCHIVE_DIR="/etc/letsencrypt/archive/${SERVER_NAME}"
RENEW_FILE="/etc/letsencrypt/renewal/${SERVER_NAME}.conf"
FULL="${LIVE_DIR}/fullchain.pem"
PRIV="${LIVE_DIR}/privkey.pem"

if [ ! -f "$FULL" ] || [ ! -f "$PRIV" ]; then
  mkdir -p "$LIVE_DIR"
  mkdir -p "$(dirname "$RENEW_FILE")"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$PRIV" -out "$FULL" -subj "/CN=${SERVER_NAME}" >/dev/null 2>&1 || true
fi

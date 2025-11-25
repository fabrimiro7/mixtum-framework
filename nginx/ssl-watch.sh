#!/bin/sh
set -eu

: "${SERVER_NAME:?SERVER_NAME missing}"

CERT_DIR="/etc/letsencrypt/live/${SERVER_NAME}"
RELOAD_FLAG="/var/www/certbot/.nginx-reload"

# 1) First deploy: wait for cert then switch to https template + reload
(
  if [ ! -f "${CERT_DIR}/fullchain.pem" ] || [ ! -f "${CERT_DIR}/privkey.pem" ]; then
    echo "[ssl-watch] Waiting for first certificate for ${SERVER_NAME}..."
    while [ ! -f "${CERT_DIR}/fullchain.pem" ] || [ ! -f "${CERT_DIR}/privkey.pem" ]; do
      sleep 2
    done
    echo "[ssl-watch] Certificate found. Switching Nginx config to HTTPS..."
    sh /docker-entrypoint.d/10-init.sh
    nginx -t && nginx -s reload || true
  fi
) &

# 2) Renew signal: reload when flag is touched by certbot deploy-hook
(
  last_mtime=0
  while :; do
    if [ -f "$RELOAD_FLAG" ]; then
      mtime="$(stat -c %Y "$RELOAD_FLAG" 2>/dev/null || stat -f %m "$RELOAD_FLAG" 2>/dev/null || echo 0)"
      if [ "$mtime" -gt "$last_mtime" ]; then
        echo "[ssl-watch] Reload requested. Reloading Nginx..."
        nginx -t && nginx -s reload || true
        last_mtime="$mtime"
      fi
    fi
    sleep 30
  done
) &

exit 0

#!/bin/sh
set -eu

: "${SERVER_NAME:?SERVER_NAME missing}"

CERT_DIR="/etc/letsencrypt/live/${SERVER_NAME}"

if [ -f "${CERT_DIR}/fullchain.pem" ] && [ -f "${CERT_DIR}/privkey.pem" ]; then
  TEMPLATE="/etc/nginx/custom-templates/default.https.conf.template"
  MODE="HTTPS"
else
  TEMPLATE="/etc/nginx/custom-templates/default.http.conf.template"
  MODE="HTTP_ONLY"
fi

envsubst '$SERVER_NAME' < "$TEMPLATE" > /etc/nginx/conf.d/default.conf
echo "Nginx config created for ${SERVER_NAME} (${MODE})"

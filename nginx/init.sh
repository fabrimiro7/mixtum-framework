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

# Check if metabase service is available (only for HTTPS template)
TEMP_TEMPLATE="$TEMPLATE"
if [ "$MODE" = "HTTPS" ]; then
  # Use getent to check if metabase hostname can be resolved
  # This uses Docker's internal DNS resolver (127.0.0.11)
  if ! getent hosts metabase >/dev/null 2>&1; then
    # Metabase not available, remove metabase location blocks from template
    TEMP_TEMPLATE="/tmp/nginx_template_no_metabase"
    # Remove the metabase location blocks using awk
    # Remove everything from "# Metabase (HTTPS)" comment until we reach "  location /" (main block, not metabase)
    awk '
      /# Metabase \(HTTPS\)/ { skip=1; next }
      skip && /^  location \// && !/metabase/ { skip=0; print; next }
      !skip { print }
    ' "$TEMPLATE" > "$TEMP_TEMPLATE"
    echo "Metabase service not available, removed metabase location blocks"
  else
    echo "Metabase service available, including metabase location blocks"
  fi
fi

envsubst '$SERVER_NAME' < "$TEMP_TEMPLATE" > /etc/nginx/conf.d/default.conf
echo "Nginx config created for ${SERVER_NAME} (${MODE})"

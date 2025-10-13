#!/bin/sh
set -eu
envsubst '$SERVER_NAME' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf
echo "Nginx config created for ${SERVER_NAME}"

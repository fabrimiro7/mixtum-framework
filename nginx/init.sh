#!/bin/sh
set -eu

envsubst '$SERVER_NAME_APP $SERVER_NAME_ADMIN' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

echo "Nginx config created for APP=${SERVER_NAME_APP} and ADMIN=${SERVER_NAME_ADMIN}"

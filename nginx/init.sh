#!/bin/sh
set -eu

envsubst '$SERVER_NAME' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "Configurazione di Nginx creata per ${SERVER_NAME}"
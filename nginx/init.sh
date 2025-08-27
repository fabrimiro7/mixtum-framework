#!/bin/sh
set -eux

echo "--- Inizio script di inizializzazione Nginx ---"

# Assicura che la variabile SERVER_NAME sia presente
: "${SERVER_NAME:?SERVER_NAME is required}"

echo "SERVER_NAME impostato a: ${SERVER_NAME}"

# Crea la configurazione di Nginx dal template
envsubst '$SERVER_NAME' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "File di configurazione Nginx creato in /etc/nginx/conf.d/default.conf"
cat /etc/nginx/conf.d/default.conf

# Definisce i percorsi per i certificati
LIVE_DIR="/etc/letsencrypt/live/${SERVER_NAME}"
FULL="${LIVE_DIR}/fullchain.pem"
PRIV="${LIVE_DIR}/privkey.pem"

# Controlla se il certificato esiste
if [ ! -f "$FULL" ]; then
  echo ">>> Certificato non trovato in ${FULL}. Generazione di un certificato fittizio..."
  
  # Crea la directory, se non esiste
  mkdir -p "$LIVE_DIR"
  
  # Esegui il comando openssl e MOSTRA L'OUTPUT in caso di errori
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$PRIV" -out "$FULL" -subj "/CN=${SERVER_NAME}"
    
  echo ">>> Comando openssl completato."
  echo ">>> Verifico i file creati nel volume:"
  ls -lR /etc/letsencrypt
else
  echo ">>> Certificato trovato. Salto la generazione."
fi

echo "--- Fine script. Avvio di Nginx... ---"
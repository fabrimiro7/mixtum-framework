# Mixtum Framework

🚀 Deployment (DEV + PROD with automatic SSL)
---------------------------------------------

This repository uses Docker Compose with:

*   **DEV (local)**: HTTP-only, no SSL, static Nginx configuration.
*   **PROD (server)**: Let’s Encrypt SSL **automatically on first deploy** + **auto-renew** with Nginx reload.

* * *

✅ Requirements
==============

*   Docker Engine + Docker Compose plugin (`docker compose`)
*   (PROD) Domain DNS pointing to the server
*   (PROD) Open inbound ports: **80** and **443**

* * *

🧪 DEV (Local)
==============

In DEV, `docker-compose.override.yml` is automatically applied (HTTP-only).

### Start (backend-only)

    docker compose --profile backend up -d --build

### Logs

    docker compose logs -f

### Stop

    docker compose down

### Full reset (removes volumes, including the DB)

    docker compose down -v

**Access**: `http://localhost/`

### Frontend (optional)

For local frontend development, use `ng serve` (recommended) and point it to the backend:

    cd frontend
    npm install
    npm start

Then configure the API base URL in your Angular environment to `http://localhost:8000` (or use a proxy config).

* * *

🌍 PROD (Server) — Automatic SSL + Auto-renew
=============================================

1) Configure `.env`
-------------------

Create/fill the `.env` file in the project root with at least:

    SERVER_NAME=admin-ticket.efestodev.com
    CERTBOT_EMAIL=you@domain.com
    
    POSTGRES_DB=mixtumdb
    POSTGRES_USER=mixtumuser
    POSTGRES_PASSWORD=a_strong_password
    
    # Optional: initial test to avoid Let's Encrypt rate limits
    # CERTBOT_STAGING=1

2) Script permissions (one-time)
--------------------------------

    chmod +x deploy.sh nginx/init.sh nginx/ssl-watch.sh certbot/entrypoint.sh scripts/entrypoint.sh

3) Deploy with a single command (backend-only)
----------------------------------------------

    ./deploy.sh

To serve the SPA from the nginx container, set the profile:

    DEPLOY_PROFILE=frontend ./deploy.sh

### Docker commands (PROD)

Backend-only (explicit):

    docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile backend up -d --build

Frontend-in-container:

    docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile frontend up -d --build

What `deploy.sh` does:

*   Builds and starts the stack in PROD mode (`docker-compose.yml` + `docker-compose.prod.yml`)
*   Verifies Nginx (port 80) and the ACME challenge webroot
*   Issues the SSL certificate if missing (Certbot one-shot command)
*   Reloads Nginx and automatically switches the configuration to HTTPS
*   Starts the **Certbot auto-renew loop**
*   Runs `renew --dry-run` to confirm renewals will work

**Access**: `https://$SERVER_NAME`

* * *

🌐 Frontend (optional) — Netlify
================================

Recommended split:

* Frontend: `https://ticket.efestodev.com`
* Backend/API: `https://admin-ticket.efestodev.com` (or any backend subdomain)

Backend CORS must allow the frontend origin:

    CORS_ALLOWED_ORIGINS=https://ticket.efestodev.com

In Angular, set `apiBase` to the backend URL (e.g. `https://admin-ticket.efestodev.com` or `.../api`).

* * *

🔎 Troubleshooting (PROD)
=========================

### Check services

    docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

### Nginx / Certbot logs

    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=200 nginx
    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=200 certbot

### Renew test (dry-run)

    docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm --entrypoint certbot certbot \
      renew --dry-run --webroot -w /var/www/certbot

### Common SSL issues

*   DNS record not pointing to the server
*   Port **80** not reachable from the internet (HTTP-01 challenge requirement)
*   Cloudflare / reverse proxy in front: for first issuance you may need “DNS only” (no proxy)

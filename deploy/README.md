# Deploy — reverse proxy

## Nginx

1. Build frontend: `cd apps/web && npm ci && npm run build`
2. Copy `apps/web/dist/*` → `/var/www/vrav/web/`
3. Install config: `sudo cp deploy/nginx.conf /etc/nginx/sites-available/vrav`
4. Enable site, `nginx -t`, reload
5. Certbot: `certbot --nginx -d your.domain`

## Caddy

1. Same static build to `/var/www/vrav/web`
2. Edit domain in `deploy/Caddyfile`
3. `caddy run --config deploy/Caddyfile`

## API process

Prefer `docker compose -f docker-compose.prod.yml up -d`.
API listens on `127.0.0.1:8000` (bind only localhost if proxy is on same host).

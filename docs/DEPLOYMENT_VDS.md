# Deployment — Linux VDS / VPS

## Requirements

- Ubuntu 22.04+ or Debian 12+
- Docker + Docker Compose plugin
- Domain with DNS A record
- Minimum: 2 vCPU, 4 GB RAM, 40 GB SSD (recommended: 4 vCPU, 8 GB RAM)

## 1. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
docker compose version
```

## 2. Clone and configure

```bash
git clone https://github.com/zametkikostik/VRAV-Tube-Engine-Weave.git
cd VRAV-Tube-Engine-Weave
cp .env.example .env
nano .env
```

Required production values:

```
APP_ENV=production
APP_SECRET_KEY=<openssl rand -hex 32>
APP_BASE_URL=https://your.domain
FRONTEND_URL=https://your.domain
DATABASE_URL=postgresql+asyncpg://vrav:<strong-password>@postgres:5432/vrav_tube
DATABASE_URL_SYNC=postgresql://vrav:<strong-password>@postgres:5432/vrav_tube
```

## 3. Start stack

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
```

## 4. Reverse proxy

See `deploy/nginx.conf` and `deploy/Caddyfile`. Build frontend:

```bash
cd apps/web && npm ci && npm run build
```

## 5. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 6. Backups

```bash
docker compose exec postgres pg_dump -U vrav vrav_tube > backup_$(date +%F).sql
```

## Security checklist

- [ ] Strong `APP_SECRET_KEY`
- [ ] HTTPS only
- [ ] Secrets not in git
- [ ] Postgres not exposed publicly
- [ ] Regular dependency updates

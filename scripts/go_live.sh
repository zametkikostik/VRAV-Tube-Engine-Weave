#!/usr/bin/env bash
# Production go-live helper for a host with Docker.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== VRAV Tube Engine go-live ==="

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example"
  cp .env.example .env
  if grep -q "change-me-to-a-long-random-string" .env 2>/dev/null; then
    SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i.bak "s/change-me-to-a-long-random-string/$SECRET/" .env
    echo "Generated APP_SECRET_KEY"
  fi
  echo ">>> Edit .env: set POSTGRES_PASSWORD, ROUTERAI_API_KEY, optional STRIPE_* and GOOGLE_*"
  echo ">>> Then re-run: ./scripts/go_live.sh"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found"
  exit 1
fi

echo "=== Building & starting prod stack ==="
docker compose -f docker-compose.prod.yml up -d --build

echo "=== Waiting for API health ==="
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "API is up"
    break
  fi
  sleep 2
  if [[ $i -eq 30 ]]; then
    echo "API did not become healthy in time"
    docker compose -f docker-compose.prod.yml logs api | tail -40
    exit 1
  fi
done

echo "=== E2E smoke ==="
if [[ -x ./scripts/e2e_smoke.sh ]]; then
  ./scripts/e2e_smoke.sh http://localhost:8000/api/v1 || {
    echo "E2E failed — check logs"
    exit 1
  }
fi

echo
echo "=== GO-LIVE COMPLETE ==="
echo "Health: http://localhost:8000/api/v1/health"
echo "Next: put Nginx/Caddy TLS in front"

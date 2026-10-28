#!/usr/bin/env bash
# End-to-end smoke test against a running API.
set -euo pipefail

BASE="${1:-http://localhost:8000/api/v1}"
EMAIL="e2e_$(date +%s)@example.com"
PASS="E2eTestPass123!"

echo "== Health =="
curl -sf "$BASE/health" | head -c 200
echo

echo "== Register =="
REG=$(curl -sf -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"full_name\":\"E2E User\",\"preferred_locale\":\"en\"}")
ACCESS=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "registered ok"

echo "== Me =="
curl -sf "$BASE/auth/me" -H "Authorization: Bearer $ACCESS" | head -c 200
echo

echo "E2E SMOKE partial OK (extend when full API is present)"

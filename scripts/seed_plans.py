#!/usr/bin/env python3
"""Seed subscription plans. Run inside API container or with DATABASE_URL set.

  docker compose exec api python -m scripts.seed_plans
  # or
  cd apps/api && PYTHONPATH=. python ../../scripts/seed_plans.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))


async def main() -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.seed import seed_subscription_plans

    async with AsyncSessionLocal() as db:
        n = await seed_subscription_plans(db)
        print(f"Plans created: {n}")


if __name__ == "__main__":
    asyncio.run(main())

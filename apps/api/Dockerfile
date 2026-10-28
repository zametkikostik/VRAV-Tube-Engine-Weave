FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir -e ".[dev]" \
    || pip install --no-cache-dir \
        fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic \
        pydantic pydantic-settings "python-jose[cryptography]" "passlib[argon2]" \
        httpx redis celery orjson reportlab stripe email-validator argon2-cffi greenlet

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

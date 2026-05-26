#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python scripts/seed.py

echo "Starting auth server..."
exec uvicorn main:app --host 0.0.0.0 --port "${AUTH_SERVER_PORT:-5000}"

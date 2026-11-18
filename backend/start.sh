#!/bin/bash
set -e

echo "Checking for unapplied Alembic migrations..."

if alembic history | grep "(head)"; then
    echo "Alembic migrations already up-to-date."
else
    echo "Running Alembic migrations..."
    alembic upgrade head
fi

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
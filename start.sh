#!/bin/bash
echo "⏳ Ejecutando migraciones Alembic..."
alembic upgrade head

echo "🌱 Ejecutando seeders (están dentro del env.py)..."

echo "🚀 Levantando el servidor..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
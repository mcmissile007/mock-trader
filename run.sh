#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# ── 1. Check PostgreSQL ──────────────────────────────────────
echo "🔍 Checking PostgreSQL..."
if pg_isready -h localhost -p 15432 -q 2>/dev/null; then
    echo "✅ PostgreSQL is running"
else
    echo "🐘 Starting PostgreSQL..."
    docker compose -f db/docker-compose.yaml up -d
    echo "⏳ Waiting for PostgreSQL to be ready..."
    for i in $(seq 1 20); do
        if pg_isready -h localhost -p 15432 -q 2>/dev/null; then
            echo "✅ PostgreSQL is ready"
            break
        fi
        if [ "$i" -eq 20 ]; then
            echo "❌ PostgreSQL failed to start after 20s"
            exit 1
        fi
        sleep 1
    done
fi

# ── 2. Check virtualenv ──────────────────────────────────────
echo "🔍 Checking virtualenv..."
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    if [[ -d ".venv" ]]; then
        echo "📦 Activating .venv..."
        source .venv/bin/activate
    else
        echo "❌ No .venv found. Create one with: python -m venv .venv"
        exit 1
    fi
else
    echo "✅ virtualenv active: $VIRTUAL_ENV"
fi

# ── 3. Check dependencies ────────────────────────────────────
echo "🔍 Checking dependencies..."
if ! python -c "import psycopg2, pandas, xgboost, requests" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -e . --quiet
else
    echo "✅ Dependencies installed"
fi

# ── 4. Launch trader ─────────────────────────────────────────
echo ""
echo "🚀 Starting Mock Trader..."
echo "════════════════════════════════════════════════════"
PYTHONPATH=src exec python scripts/main.py "$@"

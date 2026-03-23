#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# ── 1. Check PostgreSQL ──────────────────────────────────────
echo "🔍 Checking PostgreSQL..."
if ! docker compose -f db/docker-compose.yaml ps --status running 2>/dev/null | grep -q postgres; then
    echo "🐘 Starting PostgreSQL..."
    docker compose -f db/docker-compose.yaml up -d
    echo "⏳ Waiting for PostgreSQL to be ready..."
    for i in $(seq 1 15); do
        if docker compose -f db/docker-compose.yaml exec -T postgres pg_isready -q 2>/dev/null; then
            break
        fi
        sleep 1
    done
else
    echo "✅ PostgreSQL is running"
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

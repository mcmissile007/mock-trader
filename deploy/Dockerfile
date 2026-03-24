# ── Mock Trader ── Python 3.12 on Debian Bookworm slim ──
FROM python:3.12-slim-bookworm AS base

# Prevent Python from writing .pyc and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for psycopg2-binary
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python dependencies first (layer cache) ─────────
COPY pyproject.toml ./
RUN pip install --no-cache-dir . 2>/dev/null || true
# Full install after copying source
COPY src/ src/
RUN pip install --no-cache-dir -e .

# ── Copy scripts ─────────────────────────────────────────────
COPY scripts/ scripts/

# ── Create dirs for runtime ──────────────────────────────────
RUN mkdir -p logs data/models

# ── Set PYTHONPATH so scripts can import src modules ─────────
ENV PYTHONPATH=/app/src

# ── Default command ──────────────────────────────────────────
CMD ["python", "scripts/main.py"]

# ─── Build Stage ──────────────────────────────────────────────
FROM python:3.11-slim AS backend

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create cache and data directories
RUN mkdir -p /tmp/cache/gene /tmp/cache/variant /tmp/cache/drug \
    /tmp/cache/disease /tmp/cache/pathway /tmp/cache/network /tmp/cache/search

# Environment
ENV CACHE_DIR=/tmp/cache
ENV LOG_LEVEL=INFO
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}

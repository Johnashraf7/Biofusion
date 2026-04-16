# ─── BioFusion Backend — Hugging Face Spaces Compatible ──────
FROM python:3.11-slim

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
ENV PORT=7860

EXPOSE 7860

# Run on port 7860 (Hugging Face default)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

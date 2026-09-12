FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="Financial Access Intelligence Layer <fail@open-source.dev>"
LABEL description="Financial Access Intelligence Layer — Open Payments / Interledger"
LABEL version="0.1.0"

# Security: run as non-root
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi[standard]==0.115.0 \
    uvicorn[standard]==0.30.6 \
    httpx==0.27.0 \
    pydantic==2.9.2 \
    sqlalchemy[asyncio]==2.0.35 \
    asyncpg==0.29.0 \
    redis==5.1.0 \
    structlog==24.4.0 \
    prometheus-client==0.21.0 \
    cryptography==43.0.1

# Copy source code
COPY src/ ./src/
COPY apps/ ./apps/

# Ensure src is importable
ENV PYTHONPATH=/app

# Switch to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI application
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

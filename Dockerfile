# ==============================================================================
# Build Stage: Dependency Compilation and Virtual Environment Installation
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools and uv package manager
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for high-speed dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency manifests
COPY pyproject.toml README.md ./

# Create virtual environment and install production dependencies
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install --no-cache-dir .

# ==============================================================================
# Final Stage: Production Runtime Image
# ==============================================================================
FROM python:3.12-slim AS runner

LABEL maintainer="Financial Access Intelligence Team <fail@open-source.org>"
LABEL description="Financial Access Intelligence Layer (FAIL) - Multi-Dimensional FAI Engine"
LABEL version="0.1.0"

# Security: Non-root user setup
RUN groupadd --system appgroup && \
    useradd --system --uid 10001 --gid appgroup appuser

WORKDIR /app

# Install minimal runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy application source code
COPY src/ /app/src/
COPY apps/ /app/apps/

# Set file permissions for non-root appuser
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

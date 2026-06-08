# Backend Dockerfile for WOO API
# Multi-stage uv build for a smaller, reproducible final image.

FROM python:3.11-slim AS builder

# Pinned uv binary (copied from the official image — no curl|sh bootstrap).
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /usr/local/bin/

# Build deps needed to compile any sdists in the dependency tree.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# uv settings: copy wheels into the venv (layer-friendly), compile bytecode,
# and never reach back to a managed Python — use the image's interpreter.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# Install dependencies first (cached unless the lock changes), without the
# project itself, and without dev tools.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Now add the application code and install the project into the same venv.
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- Final stage ----
FROM python:3.11-slim

# Patch OS packages (closes Trivy HIGH/CRITICAL base-image findings) + curl for
# the health check.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security.
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy the resolved virtualenv and the application code from the builder.
COPY --from=builder --chown=appuser:appuser /app /app

# Put the venv on PATH so `python`/`uvicorn` resolve to it.
ENV PATH=/app/.venv/bin:$PATH

USER appuser

# Expose port (must match docker-compose)
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5002/api/helloworld || exit 1

# Run the application
CMD ["python", "-m", "server"]

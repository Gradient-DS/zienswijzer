# Backend Dockerfile for WOO API
# Multi-stage uv build. The venv is resolved on a slim Python builder, then run
# on a Chainguard Wolfi base.
#
# Why Wolfi for the runtime: Debian (and Debian-based distroless) ship HIGH/
# CRITICAL CVEs with no available fix (e.g. perl-base CVE-2026-8376 @ 9.8,
# ncurses CVE-2025-69720 @ 7.8), so they cannot reach zero Trivy HIGH/CRITICAL.
# Wolfi is glibc-based (manylinux wheels for torch/spacy/etc. work unchanged)
# and is maintained to zero known CVEs.

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

# ---- Final stage: Chainguard Wolfi (zero-CVE, glibc) ----
FROM cgr.dev/chainguard/wolfi-base

# Python 3.11 (ABI-compatible with the builder's 3.11 venv) plus the shared
# libraries the native wheels link against (torch/spacy/sentencepiece).
RUN apk add --no-cache python-3.11 libstdc++ libgomp libgcc

# Non-root user for security (uid 1000 matches the chart securityContext).
RUN adduser -D -u 1000 appuser

WORKDIR /app

# Copy the resolved virtualenv and the application code from the builder.
COPY --from=builder --chown=appuser:appuser /app /app

# Relocate the uv venv onto Wolfi's interpreter: repoint the bin symlinks and
# rewrite pyvenv.cfg `home` so CPython finds its stdlib and processes the venv
# site (including the editable project install).
RUN set -eux; \
    py=/usr/bin/python3.11; \
    ver="$($py -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])')"; \
    ln -sf "$py" /app/.venv/bin/python3.11; \
    ln -sf python3.11 /app/.venv/bin/python3; \
    ln -sf python3.11 /app/.venv/bin/python; \
    printf 'home = /usr/bin\ninclude-system-site-packages = false\nversion = %s\n' "$ver" > /app/.venv/pyvenv.cfg

# Put the venv on PATH so `python` resolves to it.
ENV PATH=/app/.venv/bin:$PATH

USER appuser

# Expose port (the app serves uvicorn on 8000; matches chart service.api.port)
EXPOSE 8000

# Health check (Wolfi has no curl; use the stdlib over the /health route).
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=5).status==200 else 1)"]

# Run the application
CMD ["python", "-m", "server"]

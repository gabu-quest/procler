# Procler - LLM-first process manager
# Multi-stage build for smaller image

# Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Build Python app
FROM python:3.12-slim AS builder

# Install uv for fast dependency resolution
RUN pip install uv

WORKDIR /app
COPY pyproject.toml ./
COPY procler/ ./procler/

# Install dependencies
RUN uv pip install --system --no-cache .

# Final image
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash procler
USER procler
WORKDIR /home/procler

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/procler /usr/local/bin/procler

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /home/procler/static

# Copy application
COPY --chown=procler:procler procler/ /home/procler/procler/

# Copy static files to the right location
RUN mkdir -p /home/procler/procler/static && \
    cp -r /home/procler/static/* /home/procler/procler/static/ 2>/dev/null || true

# Environment variables
ENV PROCLER_LOG_LEVEL=INFO
ENV PROCLER_LOG_ROTATION_INTERVAL=3600
ENV PROCLER_MAX_LOGS_PER_PROCESS=10000

# Data directory (mount as volume for persistence)
VOLUME /home/procler/.procler

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the server
CMD ["python", "-m", "procler", "serve", "--host", "0.0.0.0", "--port", "8000"]

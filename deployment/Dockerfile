# syntax=docker/dockerfile:1

# ==============================================================
# SEAM (Autonomous Multi-Agent Framework) - Production Dockerfile
# ==============================================================

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (e.g., for unstructured or chroma)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY agents /app/agents
COPY backend /app/backend
COPY knowledge /app/knowledge
COPY orchestration /app/orchestration
COPY prompts /app/prompts
COPY rag /app/rag

# Create default directories for data persistence
RUN mkdir -p /app/knowledge/data \
    && mkdir -p /app/knowledge/validated

# Expose standard port for the API (if running FastAPI/Uvicorn)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Note: The entrypoint would typically run a FastAPI server in orchestration.
# Since SEAM is modular, this defaults to a bash shell for executing local orchestrators.
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

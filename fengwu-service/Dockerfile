FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY app.py inference_engine.py ./

# Model files will be mounted as volume at runtime
EXPOSE 8085
# Security: create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -m -s /sbin/nologin appuser && \
    chown -R appuser:appgroup /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8085/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8085"]

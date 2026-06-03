FROM nvidia/cuda:11.8-runtime-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (GPU version of onnxruntime)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir onnxruntime-gpu>=1.17.0

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8085

ENV FENGWU_USE_GPU=true \
    FENGWU_MODEL_PATH=/app/model/fengwu_v2.onnx \
    FENGWU_NUM_THREADS=4

# Model warmup on startup
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8085/health/ready || exit 1

ENTRYPOINT ["python3", "app.py"]

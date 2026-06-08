FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8091

ENV FENGLEI_API_KEY="" \
    FENGLEI_CACHE_DIR="/app/cache" \
    FENGLEI_UPDATE_INTERVAL=30 \
    FENGLEI_ENV="production" \
    CORS_ORIGINS="*"

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8091/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8091"]
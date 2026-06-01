FROM python:3.11-slim
LABEL service="edge-cloud-coordinator"
LABEL version="1.0.0"

RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir fastapi uvicorn websockets kafka-python pika 2>/dev/null || true

COPY . .
RUN chown -R appuser:appuser /app

EXPOSE 8000
EXPOSE 8765
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

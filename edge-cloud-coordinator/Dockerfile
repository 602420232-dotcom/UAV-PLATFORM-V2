# 多阶段构建：第一阶段 - 依赖安装
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/dependencies -r requirements.txt

# 安装额外依赖
RUN pip install --no-cache-dir --target=/app/dependencies fastapi uvicorn websockets kafka-python pika

# 第二阶段 - 运行时
FROM python:3.11-slim

LABEL service="edge-cloud-coordinator"
LABEL version="1.0.0"

RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser

WORKDIR /app

# 从builder阶段复制依赖
COPY --from=builder /app/dependencies /usr/local/lib/python3.11/site-packages

# 复制应用代码
COPY . .
RUN chown -R appuser:appuser /app

EXPOSE 8000
EXPOSE 8765

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
# 多阶段构建：第一阶段 - 基础依赖安装
FROM nvidia/cuda:11.8-runtime-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY fengwu-service/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# GPU版本安装
RUN pip3 install --no-cache-dir onnxruntime-gpu>=1.17.0

# CPU版本（无GPU环境使用）
FROM python:3.11-slim AS cpu-base
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY fengwu-service/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir onnxruntime>=1.17.0

# 第二阶段 - 运行时（默认使用GPU版本）
FROM base AS runtime

WORKDIR /app

COPY --from=base /usr/local/lib/python3/dist-packages /usr/local/lib/python3/dist-packages
COPY --from=base /usr/bin/python3 /usr/bin/python3
COPY --from=base /usr/bin/pip3 /usr/bin/pip3

COPY fengwu-service/ .

RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8085

ENV FENGWU_USE_GPU=true \
    FENGWU_MODEL_PATH=/app/model/fengwu_v2.onnx \
    FENGWU_NUM_THREADS=4

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -sf http://localhost:8085/health || exit 1

ENTRYPOINT ["python3", "app.py"]

# CPU版本构建目标
FROM cpu-base AS cpu-runtime
WORKDIR /app
COPY --from=cpu-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY fengwu-service/ .
RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser
EXPOSE 8085
ENV FENGWU_USE_GPU=false \
    FENGWU_MODEL_PATH=/app/model/fengwu_v2.onnx \
    FENGWU_NUM_THREADS=4
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8085/health/ready || exit 1
ENTRYPOINT ["python3", "app.py"]
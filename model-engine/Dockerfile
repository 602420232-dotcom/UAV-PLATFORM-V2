FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libeccodes-dev libeccodes0 \
    gcc g++ wget curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || \
    pip install --no-cache-dir numpy scipy torch --only-binary=:all:

# model-engine 代码
COPY . /app/model-engine/

# 原项目桥接: 保留原路径引用，Docker 内用 symlink 映射
RUN mkdir -p /legacy && \
    ln -sf /app/model-engine/integration/bridge.py /legacy/ && \
    ln -sf /app/model-engine/integration/adapter.py /legacy/

# 原 meteor-forecast 代码通过 volume 运行时挂载 (不打包进镜像)
# docker run -v /path/to/meteor-forecast-service:/legacy/meteor-forecast-service

ENV PYTHONPATH=/app/model-engine:/legacy:$PYTHONPATH
RUN mkdir -p /app/models

EXPOSE 8087
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8087/health || exit 1

CMD ["uvicorn", "model-engine.api.main:app", "--host", "0.0.0.0", "--port", "8087"]

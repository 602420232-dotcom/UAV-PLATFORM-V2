# ============================================================
# Algorithm Engine (Python) Dockerfile
# ============================================================
# Python 算法引擎 - 支持 5DVAR/EnKF/Hybrid/Enhanced Bayesian 等同化算法
# 以及 VRPTW/DE-RRT*/DWA/MPC 等路径规划算法
# ============================================================

# Stage 1: 依赖安装
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装编译依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ gfortran libopenblas-dev && \
    rm -rf /var/lib/apt/lists/*

# 先复制依赖文件以利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: 运行时镜像
FROM python:3.11-slim

LABEL maintainer="UAV Platform Team"
LABEL description="UAV Platform V2 - Algorithm Engine (Python)"

# 安装运行时依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libopenblas-dev && \
    rm -rf /var/lib/apt/lists/*

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 创建非 root 用户
RUN groupadd -r uav && useradd -r -g uav -d /app -s /sbin/nologin uav

WORKDIR /app

# 从构建阶段复制已安装的 Python 包
COPY --from=builder /install /usr/local

# 复制应用代码
COPY . .

# 设置文件权限
RUN chown -R uav:uav /app

USER uav

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 9090

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:9090/health || exit 1

# 启动命令
CMD ["python", "-m", "algorithm_engine.main"]

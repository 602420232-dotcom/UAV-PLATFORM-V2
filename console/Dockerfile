# ============================================================
# Console (Frontend) Dockerfile
# ============================================================

# Stage 1: 前端构建
FROM node:20-alpine AS builder

WORKDIR /build

# 先复制依赖文件以利用 Docker 缓存层
COPY package.json package-lock.json* ./

RUN npm ci

# 复制源代码
COPY . .

# 构建
RUN npm run build

# Stage 2: Nginx 托管静态文件
FROM nginx:alpine

LABEL maintainer="UAV Platform Team"
LABEL description="UAV Platform V2 - Developer Console (Frontend)"

# 设置时区
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apk del tzdata

# 删除默认 Nginx 配置
RUN rm -rf /usr/share/nginx/html/*

# 复制构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制 SPA 路由支持文件
COPY --from=builder /build/public /usr/share/nginx/public

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

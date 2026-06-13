# ============================================================
# UAV Platform V2 - Java 微服务多阶段构建模板
# ============================================================
# 使用方法: 各微服务的 Dockerfile 通过 ARG 传入服务名称引用此模板
# ============================================================

# Stage 1: Maven 构建
FROM eclipse-temurin:21-jdk AS builder

WORKDIR /build

# 安装必要工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 先复制 pom.xml 以利用 Docker 缓存层
COPY pom.xml .
COPY common/common-core/pom.xml common/common-core/
COPY common/common-security/pom.xml common/common-security/
COPY common/common-resilience/pom.xml common/common-resilience/
COPY common/common-web/pom.xml common/common-web/

# 下载依赖（利用缓存）
RUN mvn dependency:go-offline -B || true

# 复制源代码
COPY . .

# 构建指定服务
ARG SERVICE_NAME
ARG SERVICE_DIR
RUN mvn package -pl ${SERVICE_DIR} -am -DskipTests -B

# Stage 2: 运行时镜像
FROM eclipse-temurin:21-jre-alpine

LABEL maintainer="UAV Platform Team"
LABEL description="UAV Platform V2 Java Microservice"

# 安装必要工具（curl 用于健康检查）
RUN apk add --no-cache curl tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apk del tzdata

# 创建非 root 用户
RUN addgroup -S uav && adduser -S uav -G uav

WORKDIR /app

# 从构建阶段复制 JAR
ARG SERVICE_NAME
ARG SERVICE_DIR
COPY --from=builder /build/${SERVICE_DIR}/target/${SERVICE_NAME}*.jar app.jar

# 设置文件权限
RUN chown -R uav:uav /app

USER uav

# JVM 参数
ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC -XX:+UseContainerSupport -Djava.security.egd=file:/dev/./urandom"

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8080/actuator/health || exit 1

# 启动命令
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]

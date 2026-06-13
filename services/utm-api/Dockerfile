# ============================================================
# UTM API Dockerfile
# ============================================================
FROM eclipse-temurin:21-jdk AS builder

WORKDIR /build

COPY pom.xml .
COPY common/common-core/pom.xml common/common-core/
COPY common/common-security/pom.xml common/common-security/
COPY common/common-resilience/pom.xml common/common-resilience/
COPY common/common-web/pom.xml common/common-web/
COPY services/utm-api/pom.xml services/utm-api/

RUN mvn dependency:go-offline -B -pl services/utm-api -am || true

COPY . .
RUN mvn package -pl services/utm-api -am -DskipTests -B

FROM eclipse-temurin:21-jre-alpine

LABEL maintainer="UAV Platform Team"
LABEL description="UAV Platform V2 - UTM API"

RUN apk add --no-cache curl tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apk del tzdata

RUN addgroup -S uav && adduser -S uav -G uav

WORKDIR /app

COPY --from=builder /build/services/utm-api/target/utm-api*.jar app.jar

RUN chown -R uav:uav /app

USER uav

ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC -XX:+UseContainerSupport -Djava.security.egd=file:/dev/./urandom"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]

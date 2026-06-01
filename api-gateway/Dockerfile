FROM maven:3.8.6-openjdk-17-slim AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests -B

FROM openjdk:17-jre-slim
RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
RUN chown appuser:appuser app.jar
EXPOSE 8088
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8088/actuator/health || wget -qO- http://localhost:8088/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]

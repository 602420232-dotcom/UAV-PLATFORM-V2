FROM maven:3.8.6-openjdk-17-slim AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests -B

FROM openjdk:17-jre-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip netcdf-bin curl && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser
COPY --from=builder /build/target/*.jar app.jar
COPY src/main/python/ /app/python/
RUN pip3 install --no-cache-dir -r /app/python/requirements.txt 2>/dev/null || true
RUN chown -R appuser:appuser /app
ENV PYTHONPATH=/app/python
EXPOSE 8081
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8081/actuator/health || wget -qO- http://localhost:8081/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]

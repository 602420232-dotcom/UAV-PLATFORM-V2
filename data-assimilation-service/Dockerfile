FROM maven:3.9.9-eclipse-temurin-17 AS builder
# First install the parent POM from the project root
WORKDIR /build-parent
COPY pom.xml .
RUN mvn install -N -B -q

# Build and install common-utils (shared library)
WORKDIR /build-common
COPY common-utils/pom.xml .
COPY common-utils/src ./src
RUN mvn install -DskipTests -B -q

# Now build the service
WORKDIR /build
COPY data-assimilation-service/pom.xml .
RUN mvn dependency:go-offline -B
COPY data-assimilation-service/src ./src
RUN mvn clean package -DskipTests -B

FROM eclipse-temurin:17-jre
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip curl && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser
COPY --from=builder /build/target/*.jar app.jar
COPY data-assimilation-service/src/main/python/ /app/python/
RUN pip3 install --no-cache-dir numpy scipy
RUN chown -R appuser:appuser /app
ENV PYTHONPATH=/app/python
RUN mkdir -p /logs && chown appuser:appuser /logs
EXPOSE 8084
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8084/actuator/health || wget -qO- http://localhost:8084/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]

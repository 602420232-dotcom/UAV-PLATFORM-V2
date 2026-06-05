FROM maven:3.8.6-openjdk-17-slim AS builder
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
COPY api-gateway/pom.xml .
RUN mvn dependency:go-offline -B
COPY api-gateway/src ./src
RUN mvn clean package -DskipTests -B

FROM eclipse-temurin:17-jre
RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
RUN mkdir -p /logs /app/logs && chown -R appuser:appuser /app && chown appuser:appuser /logs
EXPOSE 8088
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8088/actuator/health || wget -qO- http://localhost:8088/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]

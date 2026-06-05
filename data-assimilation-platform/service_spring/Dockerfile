FROM eclipse-temurin:17-jre
RUN groupadd -r appuser && useradd -r -g appuser -m -s /sbin/nologin appuser
WORKDIR /app
COPY target/*.jar app.jar
RUN chown appuser:appuser app.jar
EXPOSE 8080
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8080/actuator/health || wget -qO- http://localhost:8080/actuator/health || exit 1
CMD ["java", "-jar", "app.jar"]

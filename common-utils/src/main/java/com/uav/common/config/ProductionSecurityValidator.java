package com.uav.common.config;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Configuration
@Profile("prod")
public class ProductionSecurityValidator {

    private static final List<String> REQUIRED_ENV_PATTERNS = Arrays.asList(
            "CHANGE_ME",
            "changeme",
            "password",
            "secret",
            "123456",
            "qwerty"
    );

    @Value("${spring.profiles.active:}")
    private String activeProfile;

    @Value("${DB_PASSWORD:}")
    private String dbPassword;

    @Value("${JWT_SECRET:}")
    private String jwtSecret;

    @Value("${SECURITY_USER_PASSWORD:}")
    private String securityPassword;

    @Value("${GRAFANA_ADMIN_PASSWORD:}")
    private String grafanaPassword;

    @Value("${spring.datasource.password:}")
    private String datasourcePassword;

    @Value("${spring.redis.password:}")
    private String redisPassword;

    @Value("${spring.rabbitmq.password:}")
    private String rabbitmqPassword;

    @PostConstruct
    public void validateProductionSecurity() {
        log.info("Validating production environment security settings...");

        Map<String, String> envVars = Map.of(
                "DB_PASSWORD", dbPassword,
                "JWT_SECRET", jwtSecret,
                "SECURITY_USER_PASSWORD", securityPassword,
                "GRAFANA_ADMIN_PASSWORD", grafanaPassword,
                "spring.datasource.password", datasourcePassword,
                "spring.redis.password", redisPassword,
                "spring.rabbitmq.password", rabbitmqPassword
        );

        List<String> violations = envVars.entrySet().stream()
                .filter(entry -> isInvalidValue(entry.getValue()))
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());

        if (!violations.isEmpty()) {
            String errorMsg = String.format(
                    "Production security validation FAILED! The following critical environment variables contain insecure placeholder values: %s%n" +
                    "Please update these values in your environment configuration before deploying to production.",
                    violations
            );
            log.error(errorMsg);
            throw new IllegalStateException(errorMsg);
        }

        if (jwtSecret != null && jwtSecret.length() < 64) {
            String errorMsg = "JWT_SECRET must be at least 64 characters for HS512 algorithm";
            log.error(errorMsg);
            throw new IllegalStateException(errorMsg);
        }

        log.info("Production environment security validation PASSED");
    }

    private boolean isInvalidValue(String value) {
        if (value == null || value.isBlank()) {
            return true;
        }
        String lowerValue = value.toLowerCase();
        return REQUIRED_ENV_PATTERNS.stream()
                .anyMatch(pattern -> lowerValue.contains(pattern.toLowerCase()));
    }
}
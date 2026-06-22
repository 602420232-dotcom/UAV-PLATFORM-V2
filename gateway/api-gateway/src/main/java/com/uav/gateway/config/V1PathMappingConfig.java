package com.uav.gateway.config;

import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.StringUtils;

import javax.annotation.PostConstruct;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * V1 to V2 Path Mapping Configuration
 *
 * <p>Defines mapping rules for converting V1 API paths and parameters to V2 format.
 * Loaded from application.yml under the {@code gateway.v1.mapping} prefix.</p>
 *
 * <p>Supported mapping types:
 * <ul>
 *   <li><b>Path rewrite:</b> {@code /api/v1/weather/point} → {@code /api/v2/weather/point}</li>
 *   <li><b>Parameter rename:</b> {@code lat} → {@code latitude}, {@code lon} → {@code longitude}</li>
 *   <li><b>Parameter transform:</b> value conversion between V1 and V2 formats</li>
 *   <li><b>Header mapping:</b> V1 headers to V2 headers</li>
 * </ul>
 *
 * <p>Example YAML configuration:
 * <pre>
 * gateway:
 *   v1:
 *     mapping:
 *       enabled: true
 *       path-rules:
 *         - name: weather-point
 *           v1-pattern: /api/v1/weather/point
 *           v2-template: /api/v2/weather/point
 *       param-rules:
 *         - name: coordinates
 *           v1-name: lat
 *           v2-name: latitude
 *         - name: coordinates-lon
 *           v1-name: lon
 *           v2-name: longitude
 * </pre>
 */
@Slf4j
@Configuration
@ConfigurationProperties(prefix = "gateway.v1.mapping")
public class V1PathMappingConfig {

    /**
     * Enable/disable V1 path mapping
     */
    private boolean enabled = true;

    /**
     * Path rewrite rules
     */
    private List<PathRule> pathRules = new ArrayList<>();

    /**
     * Parameter mapping rules
     */
    private List<ParamRule> paramRules = new ArrayList<>();

    /**
     * Header mapping rules
     */
    private List<HeaderRule> headerRules = new ArrayList<>();

    // Compiled patterns for efficient matching
    private final Map<String, Pattern> compiledPatterns = new HashMap<>();

    @PostConstruct
    public void init() {
        if (!enabled) {
            log.info("[V1-MAPPING] V1 path mapping is disabled");
            return;
        }

        // Compile path patterns
        if (pathRules != null) {
            for (PathRule rule : pathRules) {
                if (StringUtils.hasText(rule.getV1Pattern())) {
                    compiledPatterns.put(rule.getName(),
                            Pattern.compile(rule.getV1Pattern()));
                }
            }
            log.info("[V1-MAPPING] Loaded {} path rules", pathRules.size());
        }

        if (paramRules != null) {
            log.info("[V1-MAPPING] Loaded {} parameter rules", paramRules.size());
        }

        if (headerRules != null) {
            log.info("[V1-MAPPING] Loaded {} header rules", headerRules.size());
        }
    }

    /**
     * Map a V1 path to V2 path
     *
     * @param v1Path the original V1 path
     * @return the mapped V2 path, or original path if no rule matches
     */
    public String mapPath(String v1Path) {
        if (!enabled || pathRules == null) {
            return v1Path;
        }

        for (PathRule rule : pathRules) {
            if (!rule.isEnabled()) {
                continue;
            }

            Pattern pattern = compiledPatterns.get(rule.getName());
            if (pattern == null) {
                continue;
            }

            Matcher matcher = pattern.matcher(v1Path);
            if (matcher.matches() || matcher.find()) {
                String v2Path = applyTemplate(rule.getV2Template(), matcher);
                log.debug("[V1-MAPPING] Path mapped: {} → {} (rule={})",
                        v1Path, v2Path, rule.getName());
                return v2Path;
            }
        }

        // Default: simple version replacement if no explicit rule matches
        if (v1Path.startsWith("/api/v1/")) {
            return v1Path.replaceFirst("/api/v1/", "/api/v2/");
        }

        return v1Path;
    }

    /**
     * Map V1 query parameters to V2 format
     *
     * @param params original parameters map
     * @return mapped parameters map
     */
    public Map<String, String> mapParams(Map<String, String> params) {
        if (!enabled || paramRules == null || params == null) {
            return params;
        }

        Map<String, String> result = new HashMap<>(params);

        for (ParamRule rule : paramRules) {
            if (!rule.isEnabled()) {
                continue;
            }

            String v1Value = result.get(rule.getV1Name());
            if (v1Value != null) {
                // Remove old parameter name
                result.remove(rule.getV1Name());

                // Apply value transformation if configured
                String v2Value = applyValueTransform(v1Value, rule.getTransform());

                // Add with new parameter name
                result.put(rule.getV2Name(), v2Value);

                log.debug("[V1-MAPPING] Param mapped: {}={} → {}={} (rule={})",
                        rule.getV1Name(), v1Value, rule.getV2Name(), v2Value, rule.getName());
            }
        }

        return result;
    }

    /**
     * Map V1 headers to V2 headers
     *
     * @param headers original headers map
     * @return mapped headers map
     */
    public Map<String, String> mapHeaders(Map<String, String> headers) {
        if (!enabled || headerRules == null || headers == null) {
            return headers;
        }

        Map<String, String> result = new HashMap<>(headers);

        for (HeaderRule rule : headerRules) {
            if (!rule.isEnabled()) {
                continue;
            }

            String v1Value = result.get(rule.getV1Name());
            if (v1Value != null) {
                result.remove(rule.getV1Name());

                String v2Value = applyValueTransform(v1Value, rule.getTransform());
                result.put(rule.getV2Name(), v2Value);

                log.debug("[V1-MAPPING] Header mapped: {}={} → {}={} (rule={})",
                        rule.getV1Name(), v1Value, rule.getV2Name(), v2Value, rule.getName());
            }
        }

        return result;
    }

    /**
     * Apply template with regex group replacements
     */
    private String applyTemplate(String template, Matcher matcher) {
        String result = template;
        for (int i = 0; i <= matcher.groupCount(); i++) {
            String groupValue = matcher.group(i);
            if (groupValue != null) {
                result = result.replace("{" + i + "}", groupValue);
            }
        }
        return result;
    }

    /**
     * Apply value transformation
     */
    private String applyValueTransform(String value, String transform) {
        if (!StringUtils.hasText(transform)) {
            return value;
        }

        switch (transform.toLowerCase()) {
            case "uppercase":
                return value.toUpperCase();
            case "lowercase":
                return value.toLowerCase();
            case "boolean-string":
                return "1".equals(value) || "true".equalsIgnoreCase(value) ? "true" : "false";
            case "int-boolean":
                return "true".equalsIgnoreCase(value) ? "1" : "0";
            default:
                return value;
        }
    }

    // ============ Getters and Setters ============

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public List<PathRule> getPathRules() {
        return pathRules;
    }

    public void setPathRules(List<PathRule> pathRules) {
        this.pathRules = pathRules;
    }

    public List<ParamRule> getParamRules() {
        return paramRules;
    }

    public void setParamRules(List<ParamRule> paramRules) {
        this.paramRules = paramRules;
    }

    public List<HeaderRule> getHeaderRules() {
        return headerRules;
    }

    public void setHeaderRules(List<HeaderRule> headerRules) {
        this.headerRules = headerRules;
    }

    // ============ Rule Classes ============

    @Data
    public static class PathRule {
        /**
         * Rule name for identification
         */
        private String name;

        /**
         * Whether this rule is enabled
         */
        private boolean enabled = true;

        /**
         * V1 path regex pattern
         * Example: {@code /api/v1/weather/point}
         */
        private String v1Pattern;

        /**
         * V2 path template with group placeholders
         * Example: {@code /api/v2/weather/point}
         */
        private String v2Template;

        /**
         * Optional description
         */
        private String description;
    }

    @Data
    public static class ParamRule {
        /**
         * Rule name for identification
         */
        private String name;

        /**
         * Whether this rule is enabled
         */
        private boolean enabled = true;

        /**
         * V1 parameter name
         * Example: {@code lat}
         */
        private String v1Name;

        /**
         * V2 parameter name
         * Example: {@code latitude}
         */
        private String v2Name;

        /**
         * Value transformation type
         * Supported: uppercase, lowercase, boolean-string, int-boolean
         */
        private String transform;

        /**
         * Optional description
         */
        private String description;
    }

    @Data
    public static class HeaderRule {
        /**
         * Rule name for identification
         */
        private String name;

        /**
         * Whether this rule is enabled
         */
        private boolean enabled = true;

        /**
         * V1 header name
         */
        private String v1Name;

        /**
         * V2 header name
         */
        private String v2Name;

        /**
         * Value transformation type
         */
        private String transform;

        /**
         * Optional description
         */
        private String description;
    }
}

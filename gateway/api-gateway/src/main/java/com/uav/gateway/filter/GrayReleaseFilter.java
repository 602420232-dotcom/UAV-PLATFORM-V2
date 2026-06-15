package com.uav.gateway.filter;

import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Gray Release Filter
 * Routes requests to V2 services based on configurable gray-release rules.
 *
 * <p>Supported gray-release strategies:
 * <ul>
 *   <li>Percentage-based: user_id hash modulo 100 &lt; percentage</li>
 *   <li>Header-based: specific header key/value match</li>
 *   <li>API Key-based: specific tenant or API key routed to V2</li>
 *   <li>Cookie-based: specific cookie value</li>
 *   <li>Query Param-based: specific query parameter</li>
 * </ul>
 *
 * <p>Configuration is loaded from application.yml and can be overridden dynamically via Redis.
 * Redis key pattern: {@code gray:release:{module}} stores JSON config for hot updates.</p>
 *
 * <p>Execution order: HIGHEST_PRECEDENCE + 15 (after V1JwtConvert, before ApiVersion)</p>
 */
@Slf4j
@Component
public class GrayReleaseFilter implements GlobalFilter, Ordered {

    private static final String GRAY_HEADER_KEY = "X-Version";
    private static final String GRAY_HEADER_VALUE = "v2";
    private static final String GRAY_ROUTE_ATTR = "grayRouteToV2";
    private static final String GRAY_MODULE_ATTR = "grayModule";

    private static final String REDIS_CONFIG_PREFIX = "gray:release:";
    private static final String REDIS_GLOBAL_KEY = "gray:release:global";

    private final ReactiveStringRedisTemplate redisTemplate;

    @Value("${gateway.gray-release.enabled:false}")
    private boolean grayReleaseEnabled;

    @Value("${gateway.gray-release.default-percentage:0}")
    private int defaultPercentage;

    @Value("${gateway.gray-release.header-key:X-Version}")
    private String headerKey;

    @Value("${gateway.gray-release.header-value:v2}")
    private String headerValue;

    // Module-specific configurations (loaded from YAML)
    @Value("#{${gateway.gray-release.modules:{}}}")
    private Map<String, GrayModuleConfig> moduleConfigs;

    // In-memory cache for module configurations (merged from YAML + Redis)
    private final Map<String, GrayModuleConfig> cachedConfigs = new ConcurrentHashMap<>();

    // Module path prefixes for matching
    private static final Map<String, String> MODULE_PATH_MAP = new HashMap<>();

    static {
        MODULE_PATH_MAP.put("weather", "/api/v1/weather/");
        MODULE_PATH_MAP.put("planning", "/api/v1/planning/");
        MODULE_PATH_MAP.put("risk", "/api/v1/risk/");
        MODULE_PATH_MAP.put("observation", "/api/v1/observation/");
        MODULE_PATH_MAP.put("assimilation", "/api/v1/assimilation/");
        MODULE_PATH_MAP.put("utm", "/api/v1/utm/");
        MODULE_PATH_MAP.put("tenants", "/api/v1/tenants/");
        MODULE_PATH_MAP.put("api-keys", "/api/v1/api-keys/");
        MODULE_PATH_MAP.put("usage", "/api/v1/usage/");
        MODULE_PATH_MAP.put("platform", "/api/v1/platform/");
        MODULE_PATH_MAP.put("flight", "/api/v1/flight/");
    }

    public GrayReleaseFilter(ReactiveStringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @PostConstruct
    public void init() {
        if (moduleConfigs != null) {
            cachedConfigs.putAll(moduleConfigs);
            log.info("[GRAY-RELEASE] Loaded {} module configs from YAML", moduleConfigs.size());
        }
        log.info("[GRAY-RELEASE] Filter initialized | enabled={} | defaultPercentage={}",
                grayReleaseEnabled, defaultPercentage);
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String requestId = request.getHeaders().getFirst("X-Request-ID");
        String path = request.getURI().getPath();

        // Gray release disabled, route to V1
        if (!grayReleaseEnabled) {
            log.debug("[GRAY-RELEASE] Gray release disabled, routing to V1 | id={}", requestId);
            exchange.getAttributes().put(GRAY_ROUTE_ATTR, false);
            return chain.filter(exchange);
        }

        // Determine which module this request targets
        String module = resolveModule(path);
        if (module == null) {
            log.debug("[GRAY-RELEASE] No module matched for path={}, routing to V1 | id={}", path, requestId);
            exchange.getAttributes().put(GRAY_ROUTE_ATTR, false);
            return chain.filter(exchange);
        }

        exchange.getAttributes().put(GRAY_MODULE_ATTR, module);

        // Check if this module has gray release enabled
        GrayModuleConfig config = getModuleConfig(module);
        if (config == null || !config.isEnabled()) {
            log.debug("[GRAY-RELEASE] Module {} gray release not enabled, routing to V1 | id={}", module, requestId);
            exchange.getAttributes().put(GRAY_ROUTE_ATTR, false);
            return chain.filter(exchange);
        }

        // Evaluate gray release rules
        boolean routeToV2 = evaluateGrayRules(request, config);

        log.info("[GRAY-RELEASE] Decision | module={} | routeToV2={} | id={}", module, routeToV2, requestId);

        exchange.getAttributes().put(GRAY_ROUTE_ATTR, routeToV2);

        // Add gray route headers for downstream services
        ServerHttpRequest mutatedRequest = request.mutate()
                .header("X-Gray-Route-To-V2", String.valueOf(routeToV2))
                .header("X-Gray-Module", module)
                .build();

        return chain.filter(exchange.mutate().request(mutatedRequest).build());
    }

    /**
     * Resolve module name from request path
     */
    private String resolveModule(String path) {
        for (Map.Entry<String, String> entry : MODULE_PATH_MAP.entrySet()) {
            if (path.startsWith(entry.getValue()) || path.startsWith(entry.getValue().replace("/v1/", "/v2/"))) {
                return entry.getKey();
            }
        }
        return null;
    }

    /**
     * Get module configuration (from cache or Redis)
     */
    private GrayModuleConfig getModuleConfig(String module) {
        // First check in-memory cache
        GrayModuleConfig config = cachedConfigs.get(module);
        if (config != null) {
            return config;
        }

        // If Redis is available, try to fetch dynamic config
        if (redisTemplate != null) {
            try {
                String redisKey = REDIS_CONFIG_PREFIX + module;
                String configJson = redisTemplate.opsForValue().get(redisKey).block();
                if (StringUtils.hasText(configJson)) {
                    // Simple parsing - in production use Jackson ObjectMapper
                    config = parseSimpleConfig(configJson);
                    if (config != null) {
                        cachedConfigs.put(module, config);
                        return config;
                    }
                }
            } catch (Exception e) {
                log.warn("[GRAY-RELEASE] Failed to load config from Redis for module={}", module, e);
            }
        }

        return null;
    }

    /**
     * Evaluate all gray release rules for a request
     */
    private boolean evaluateGrayRules(ServerHttpRequest request, GrayModuleConfig config) {
        // Priority 1: Header-based routing (explicit opt-in)
        String headerVal = request.getHeaders().getFirst(config.getHeaderKey() != null ? config.getHeaderKey() : headerKey);
        if (StringUtils.hasText(headerVal)) {
            String expectedValue = config.getHeaderValue() != null ? config.getHeaderValue() : headerValue;
            if (expectedValue.equalsIgnoreCase(headerVal)) {
                log.debug("[GRAY-RELEASE] Matched header rule: {}={}", config.getHeaderKey(), headerVal);
                return true;
            }
        }

        // Priority 2: API Key / Tenant-based routing
        String apiKey = request.getHeaders().getFirst("X-API-Key");
        if (StringUtils.hasText(apiKey) && config.getApiKeys() != null && config.getApiKeys().contains(apiKey)) {
            log.debug("[GRAY-RELEASE] Matched API Key rule: {}", apiKey);
            return true;
        }

        String tenantId = request.getHeaders().getFirst("X-Tenant-ID");
        if (StringUtils.hasText(tenantId) && config.getTenants() != null && config.getTenants().contains(tenantId)) {
            log.debug("[GRAY-RELEASE] Matched Tenant rule: {}", tenantId);
            return true;
        }

        // Priority 3: Cookie-based routing
        String cookieValue = extractCookie(request, config.getCookieKey());
        if (StringUtils.hasText(cookieValue) && config.getCookieValue() != null
                && config.getCookieValue().equalsIgnoreCase(cookieValue)) {
            log.debug("[GRAY-RELEASE] Matched cookie rule: {}={}", config.getCookieKey(), cookieValue);
            return true;
        }

        // Priority 4: Query parameter-based routing
        String queryValue = request.getQueryParams().getFirst(config.getQueryParamKey());
        if (StringUtils.hasText(queryValue) && config.getQueryParamValue() != null
                && config.getQueryParamValue().equalsIgnoreCase(queryValue)) {
            log.debug("[GRAY-RELEASE] Matched query param rule: {}={}", config.getQueryParamKey(), queryValue);
            return true;
        }

        // Priority 5: Percentage-based routing (user_id hash)
        int percentage = config.getPercentage() >= 0 ? config.getPercentage() : defaultPercentage;
        if (percentage > 0) {
            String userId = extractUserId(request);
            if (StringUtils.hasText(userId)) {
                int hash = hashUserId(userId);
                boolean inGray = (hash % 100) < percentage;
                log.debug("[GRAY-RELEASE] Percentage check | userId={} | hash={} | percentage={} | inGray={}",
                        userId, hash, percentage, inGray);
                return inGray;
            }
        }

        return false;
    }

    /**
     * Extract user ID from request (header, JWT, or API key)
     */
    private String extractUserId(ServerHttpRequest request) {
        // Try X-User-ID header first
        String userId = request.getHeaders().getFirst("X-User-ID");
        if (StringUtils.hasText(userId)) {
            return userId;
        }

        // Try to extract from Authorization header (JWT sub claim)
        String authHeader = request.getHeaders().getFirst("Authorization");
        if (StringUtils.hasText(authHeader) && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            // Simple extraction - in production parse JWT properly
            try {
                String[] parts = token.split("\\.");
                if (parts.length == 3) {
                    String payload = new String(java.util.Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8);
                    // Very simple JSON extraction for "sub" field
                    int subIndex = payload.indexOf("\"sub\"");
                    if (subIndex >= 0) {
                        int colonIndex = payload.indexOf(':', subIndex);
                        int quoteStart = payload.indexOf('"', colonIndex + 1);
                        int quoteEnd = payload.indexOf('"', quoteStart + 1);
                        if (quoteStart >= 0 && quoteEnd > quoteStart) {
                            return payload.substring(quoteStart + 1, quoteEnd);
                        }
                    }
                }
            } catch (Exception e) {
                log.debug("[GRAY-RELEASE] Failed to extract userId from JWT");
            }
        }

        // Fallback to API key as identity
        String apiKey = request.getHeaders().getFirst("X-API-Key");
        if (StringUtils.hasText(apiKey)) {
            return apiKey;
        }

        // Fallback to tenant ID
        String tenantId = request.getHeaders().getFirst("X-Tenant-ID");
        if (StringUtils.hasText(tenantId)) {
            return tenantId;
        }

        return null;
    }

    /**
     * Hash user ID to a number for percentage-based routing
     */
    private int hashUserId(String userId) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(userId.getBytes(StandardCharsets.UTF_8));
            // Use first 4 bytes as positive int
            return ((hash[0] & 0xFF) << 24) | ((hash[1] & 0xFF) << 16)
                    | ((hash[2] & 0xFF) << 8) | (hash[3] & 0xFF);
        } catch (NoSuchAlgorithmException e) {
            // Fallback to hashCode
            return Math.abs(userId.hashCode());
        }
    }

    /**
     * Extract cookie value by name
     */
    private String extractCookie(ServerHttpRequest request, String cookieName) {
        if (!StringUtils.hasText(cookieName)) {
            return null;
        }
        String cookieHeader = request.getHeaders().getFirst("Cookie");
        if (!StringUtils.hasText(cookieHeader)) {
            return null;
        }
        for (String cookie : cookieHeader.split(";")) {
            String[] parts = cookie.trim().split("=", 2);
            if (parts.length == 2 && parts[0].trim().equals(cookieName)) {
                return parts[1].trim();
            }
        }
        return null;
    }

    /**
     * Simple config parser for Redis JSON (production: use Jackson)
     */
    private GrayModuleConfig parseSimpleConfig(String json) {
        try {
            GrayModuleConfig config = new GrayModuleConfig();
            // Very simple JSON parsing - in production use ObjectMapper
            config.setEnabled(json.contains("\"enabled\":true"));

            int pctIdx = json.indexOf("\"percentage\":");
            if (pctIdx >= 0) {
                int endIdx = json.indexOf(",", pctIdx);
                if (endIdx < 0) endIdx = json.indexOf("}", pctIdx);
                String pctStr = json.substring(pctIdx + 14, endIdx).trim();
                config.setPercentage(Integer.parseInt(pctStr));
            }

            int hkIdx = json.indexOf("\"header-key\":");
            if (hkIdx >= 0) {
                int start = json.indexOf('"', hkIdx + 13) + 1;
                int end = json.indexOf('"', start);
                config.setHeaderKey(json.substring(start, end));
            }

            int hvIdx = json.indexOf("\"header-value\":");
            if (hvIdx >= 0) {
                int start = json.indexOf('"', hvIdx + 15) + 1;
                int end = json.indexOf('"', start);
                config.setHeaderValue(json.substring(start, end));
            }

            return config;
        } catch (Exception e) {
            log.warn("[GRAY-RELEASE] Failed to parse config JSON: {}", json, e);
            return null;
        }
    }

    /**
     * Refresh configuration from Redis (can be called by scheduled task or admin endpoint)
     */
    public Mono<Void> refreshConfigFromRedis() {
        if (redisTemplate == null) {
            return Mono.empty();
        }

        return redisTemplate.keys(REDIS_CONFIG_PREFIX + "*")
                .flatMap(key -> {
                    String module = key.substring(REDIS_CONFIG_PREFIX.length());
                    return redisTemplate.opsForValue().get(key)
                            .doOnNext(json -> {
                                GrayModuleConfig config = parseSimpleConfig(json);
                                if (config != null) {
                                    cachedConfigs.put(module, config);
                                    log.info("[GRAY-RELEASE] Refreshed config for module={} from Redis", module);
                                }
                            });
                })
                .then();
    }

    @Override
    public int getOrder() {
        // After V1JwtConvert (HIGHEST+5), before ApiVersion (HIGHEST+20)
        return Ordered.HIGHEST_PRECEDENCE + 15;
    }

    // ============ Configuration Classes ============

    @Data
    public static class GrayModuleConfig {
        private boolean enabled = false;
        private int percentage = -1;  // -1 means use default
        private String headerKey;
        private String headerValue;
        private String cookieKey;
        private String cookieValue;
        private String queryParamKey;
        private String queryParamValue;
        private List<String> apiKeys;
        private List<String> tenants;
    }
}

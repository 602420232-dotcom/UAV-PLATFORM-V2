package com.uav.gateway.filter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.data.redis.core.ReactiveStringRedisTemplate;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
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

    private static final String GRAY_ROUTE_ATTR = "grayRouteToV2";
    private static final String GRAY_MODULE_ATTR = "grayModule";

    private static final String REDIS_CONFIG_PREFIX = "gray:release:";

    private final ReactiveStringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;

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

    public GrayReleaseFilter(ReactiveStringRedisTemplate redisTemplate, ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    @PostConstruct
    public void init() {
        if (moduleConfigs != null && !moduleConfigs.isEmpty()) {
            cachedConfigs.putAll(moduleConfigs);
            log.info("[GRAY-RELEASE] Loaded {} module configs from YAML", moduleConfigs.size());
        } else {
            log.info("[GRAY-RELEASE] No module configs from YAML, using empty default");
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

        // Reactive chain: get config -> evaluate rules -> route
        return getModuleConfig(module)
                .flatMap(config -> {
                    if (!config.isEnabled()) {
                        log.debug("[GRAY-RELEASE] Module {} gray release not enabled, routing to V1 | id={}",
                                module, requestId);
                        exchange.getAttributes().put(GRAY_ROUTE_ATTR, false);
                        return chain.filter(exchange);
                    }

                    // Evaluate gray release rules
                    boolean routeToV2 = evaluateGrayRules(request, config);
                    log.info("[GRAY-RELEASE] Decision | module={} | routeToV2={} | id={}",
                            module, routeToV2, requestId);

                    exchange.getAttributes().put(GRAY_ROUTE_ATTR, routeToV2);

                    // Add gray route headers for downstream services
                    ServerHttpRequest mutatedRequest = request.mutate()
                            .header("X-Gray-Route-To-V2", String.valueOf(routeToV2))
                            .header("X-Gray-Module", module)
                            .build();

                    return chain.filter(exchange.mutate().request(mutatedRequest).build());
                })
                .switchIfEmpty(Mono.defer(() -> {
                    log.debug("[GRAY-RELEASE] No config for module={}, routing to V1 | id={}",
                            module, requestId);
                    exchange.getAttributes().put(GRAY_ROUTE_ATTR, false);
                    return chain.filter(exchange);
                }));
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
     * Get module configuration (from cache or Redis) - Reactive
     */
    private Mono<GrayModuleConfig> getModuleConfig(String module) {
        // First check in-memory cache
        GrayModuleConfig cached = cachedConfigs.get(module);
        if (cached != null) {
            return Mono.just(cached);
        }

        // If Redis is available, try to fetch dynamic config
        if (redisTemplate == null) {
            return Mono.empty();
        }

                String redisKey = REDIS_CONFIG_PREFIX + module;
                return redisTemplate.opsForValue().get(redisKey)
                        .flatMap(configJson -> {
                            if (configJson == null || configJson.isEmpty()) {
                                return Mono.empty();
                            }
                            try {
                        GrayModuleConfig config = objectMapper.readValue(configJson, GrayModuleConfig.class);
                        cachedConfigs.put(module, config);
                        log.info("[GRAY-RELEASE] Loaded config for module={} from Redis", module);
                        return Mono.just(config);
                    } catch (JsonProcessingException e) {
                        log.warn("[GRAY-RELEASE] Failed to parse config JSON for module={}: {}", module, configJson, e);
                        return Mono.empty();
                    }
                })
                .switchIfEmpty(Mono.defer(() -> {
                    log.debug("[GRAY-RELEASE] No Redis config for module={}", module);
                    return Mono.empty();
                }));
    }

    /**
     * Evaluate all gray release rules for a request
     */
    private boolean evaluateGrayRules(ServerHttpRequest request, GrayModuleConfig config) {
        // Priority 1: Header-based routing (explicit opt-in)
        String effectiveHeaderKey = config.getHeaderKey() != null ? config.getHeaderKey() : headerKey;
        if (effectiveHeaderKey != null) {
            String headerVal = request.getHeaders().getFirst(effectiveHeaderKey);
            if (headerVal != null && !headerVal.isEmpty()) {
                String expectedValue = config.getHeaderValue() != null ? config.getHeaderValue() : headerValue;
                if (expectedValue != null && expectedValue.equalsIgnoreCase(headerVal)) {
                    log.debug("[GRAY-RELEASE] Matched header rule: {}={}", effectiveHeaderKey, headerVal);
                    return true;
                }
            }
        }

        // Priority 2: API Key / Tenant-based routing
        String apiKey = request.getHeaders().getFirst("X-API-Key");
        if (apiKey != null && !apiKey.isEmpty() && config.getApiKeys() != null && config.getApiKeys().contains(apiKey)) {
            log.debug("[GRAY-RELEASE] Matched API Key rule: {}", apiKey);
            return true;
        }

        String tenantId = request.getHeaders().getFirst("X-Tenant-ID");
        if (tenantId != null && !tenantId.isEmpty() && config.getTenants() != null && config.getTenants().contains(tenantId)) {
            log.debug("[GRAY-RELEASE] Matched Tenant rule: {}", tenantId);
            return true;
        }

        // Priority 3: Cookie-based routing
        String cookieKey = config.getCookieKey();
        if (cookieKey != null && !cookieKey.isEmpty()) {
            String cookieValue = extractCookie(request, cookieKey);
            String expectedCookieValue = config.getCookieValue();
            if (cookieValue != null && !cookieValue.isEmpty() && expectedCookieValue != null
                    && expectedCookieValue.equalsIgnoreCase(cookieValue)) {
                log.debug("[GRAY-RELEASE] Matched cookie rule: {}={}", cookieKey, cookieValue);
                return true;
            }
        }

        // Priority 4: Query parameter-based routing
        String queryParamKey = config.getQueryParamKey();
        if (queryParamKey != null && !queryParamKey.isEmpty()) {
            String queryValue = request.getQueryParams().getFirst(queryParamKey);
            String expectedQueryParamValue = config.getQueryParamValue();
            if (queryValue != null && !queryValue.isEmpty() && expectedQueryParamValue != null
                    && expectedQueryParamValue.equalsIgnoreCase(queryValue)) {
                log.debug("[GRAY-RELEASE] Matched query param rule: {}={}", queryParamKey, queryValue);
                return true;
            }
        }

        // Priority 5: Percentage-based routing (user_id hash)
        int percentage = config.getPercentage() >= 0 ? config.getPercentage() : defaultPercentage;
        if (percentage > 0) {
            String userId = extractUserId(request);
            if (userId != null && !userId.isEmpty()) {
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
        if (userId != null && !userId.isEmpty()) {
            return userId;
        }

        // Try to extract from Authorization header (JWT sub claim)
        String authHeader = request.getHeaders().getFirst("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
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
        if (apiKey != null && !apiKey.isEmpty()) {
            return apiKey;
        }

        // Fallback to tenant ID
        String tenantId = request.getHeaders().getFirst("X-Tenant-ID");
        if (tenantId != null && !tenantId.isEmpty()) {
            return tenantId;
        }

        return null;
    }

    /**
     * Hash user ID to a non-negative number for percentage-based routing
     */
    private int hashUserId(String userId) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(userId.getBytes(StandardCharsets.UTF_8));
            // Use first 4 bytes as non-negative int (mask sign bit)
            int value = ((hash[0] & 0xFF) << 24) | ((hash[1] & 0xFF) << 16)
                    | ((hash[2] & 0xFF) << 8) | (hash[3] & 0xFF);
            return value & 0x7FFFFFFF; // Ensure non-negative
        } catch (NoSuchAlgorithmException e) {
            // Fallback to hashCode, ensure non-negative
            return Math.abs(userId.hashCode()) & 0x7FFFFFFF;
        }
    }

    /**
     * Extract cookie value by name
     */
    private String extractCookie(ServerHttpRequest request, String cookieName) {
        if (cookieName == null || cookieName.isEmpty()) {
            return null;
        }
        String cookieHeader = request.getHeaders().getFirst("Cookie");
        if (cookieHeader == null || cookieHeader.isEmpty()) {
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
     * Refresh configuration from Redis (can be called by scheduled task or admin endpoint)
     */
    public Mono<Void> refreshConfigFromRedis() {
        if (redisTemplate == null) {
            return Mono.empty();
        }

        return redisTemplate.keys(REDIS_CONFIG_PREFIX + "*")
                .flatMap(key -> {
                    if (key == null || key.length() <= REDIS_CONFIG_PREFIX.length()) {
                        return Mono.empty();
                    }
                    String module = key.substring(REDIS_CONFIG_PREFIX.length());
                    return redisTemplate.opsForValue().get(key)
                            .flatMap(json -> {
                                try {
                                    GrayModuleConfig config = objectMapper.readValue(json, GrayModuleConfig.class);
                                    cachedConfigs.put(module, config);
                                    log.info("[GRAY-RELEASE] Refreshed config for module={} from Redis", module);
                                    return Mono.just(config);
                                } catch (JsonProcessingException e) {
                                    log.warn("[GRAY-RELEASE] Failed to parse config for module={}: {}", module, json, e);
                                    return Mono.empty();
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

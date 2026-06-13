package com.uav.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * UTM Callback Security Filter
 * Validates UTM callbacks with IP whitelist, HMAC signature, and replay protection
 * Order: After RequestLog, before ApiVersion
 */
@Slf4j
@Component
public class UtmCallbackFilter implements GlobalFilter, Ordered {

    @Value("${gateway.utm.whitelist:}")
    private String whitelistStr;

    @Value("${gateway.utm.secret:default-secret-key}")
    private String utmSecret;

    @Value("${gateway.utm.replay-window:300}")
    private long replayWindowSeconds;

    private static final String UTM_PATH_PREFIX = "/api/v1/utm/callback";
    private static final String SIGNATURE_HEADER = "X-UTM-Signature";
    private static final String TIMESTAMP_HEADER = "X-UTM-Timestamp";
    private static final String NONCE_HEADER = "X-UTM-Nonce";

    // Replay protection: store used nonces with expiration
    private final Set<String> usedNonces = ConcurrentHashMap.newKeySet();

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();

        // Only apply to UTM callback paths
        if (!path.startsWith(UTM_PATH_PREFIX)) {
            return chain.filter(exchange);
        }

        String requestId = request.getHeaders().getFirst("X-Request-ID");
        log.info("[UTM] Validating callback request id={}", requestId);

        // 1. IP Whitelist Check
        String clientIp = getClientIp(request);
        if (!isIpWhitelisted(clientIp)) {
            log.warn("[UTM] IP not whitelisted: ip={} id={}", clientIp, requestId);
            return reject(exchange, HttpStatus.FORBIDDEN, "IP not whitelisted");
        }

        // 2. Timestamp Check (prevent replay)
        String timestampStr = request.getHeaders().getFirst(TIMESTAMP_HEADER);
        if (!isValidTimestamp(timestampStr)) {
            log.warn("[UTM] Invalid timestamp: ts={} id={}", timestampStr, requestId);
            return reject(exchange, HttpStatus.BAD_REQUEST, "Invalid or expired timestamp");
        }

        // 3. Nonce Check (prevent replay)
        String nonce = request.getHeaders().getFirst(NONCE_HEADER);
        if (!StringUtils.hasText(nonce) || usedNonces.contains(nonce)) {
            log.warn("[UTM] Invalid or reused nonce: id={}", requestId);
            return reject(exchange, HttpStatus.BAD_REQUEST, "Invalid or reused nonce");
        }

        // 4. HMAC Signature Verification
        String signature = request.getHeaders().getFirst(SIGNATURE_HEADER);
        String method = request.getMethod().name();
        String expectedSignature = generateHmac(method, path, timestampStr, nonce);

        if (!StringUtils.hasText(signature) || !signature.equals(expectedSignature)) {
            log.warn("[UTM] Invalid signature: id={}", requestId);
            return reject(exchange, HttpStatus.UNAUTHORIZED, "Invalid signature");
        }

        // Mark nonce as used
        usedNonces.add(nonce);
        log.info("[UTM] Callback validated successfully: id={}", requestId);

        return chain.filter(exchange);
    }

    private boolean isIpWhitelisted(String clientIp) {
        if (!StringUtils.hasText(whitelistStr)) {
            return true; // Allow all if no whitelist configured
        }
        List<String> whitelist = Arrays.asList(whitelistStr.split(","));
        return whitelist.stream().map(String::trim).anyMatch(ip -> ip.equals(clientIp));
    }

    private boolean isValidTimestamp(String timestampStr) {
        if (!StringUtils.hasText(timestampStr)) {
            return false;
        }
        try {
            long timestamp = Long.parseLong(timestampStr);
            long now = Instant.now().getEpochSecond();
            return Math.abs(now - timestamp) <= replayWindowSeconds;
        } catch (NumberFormatException e) {
            return false;
        }
    }

    private String generateHmac(String method, String path, String timestamp, String nonce) {
        try {
            String payload = method + ":" + path + ":" + timestamp + ":" + nonce;
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKey = new SecretKeySpec(utmSecret.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            mac.init(secretKey);
            byte[] hash = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(hash);
        } catch (Exception e) {
            log.error("[UTM] Failed to generate HMAC", e);
            return "";
        }
    }

    private String getClientIp(ServerHttpRequest request) {
        String ip = request.getHeaders().getFirst("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddress() != null
                    ? request.getRemoteAddress().getAddress().getHostAddress()
                    : "unknown";
        }
        return ip.split(",")[0].trim();
    }

    private Mono<Void> reject(ServerWebExchange exchange, HttpStatus status, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(status);
        response.getHeaders().add("Content-Type", "application/json");
        String body = String.format("{\"code\":%d,\"message\":\"%s\"}", status.value(), message);
        DataBuffer buffer = response.bufferFactory().wrap(body.getBytes(StandardCharsets.UTF_8));
        return response.writeWith(Mono.just(buffer));
    }

    @Override
    public int getOrder() {
        // After RequestLog (HIGHEST_PRECEDENCE), before ApiVersion
        return Ordered.HIGHEST_PRECEDENCE + 10;
    }
}

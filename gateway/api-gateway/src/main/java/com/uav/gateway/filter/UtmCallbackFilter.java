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
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Arrays;
import java.util.Base64;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * UTM Callback Security Filter
 * Validates UTM callbacks with IP whitelist, HMAC signature, and replay protection.
 * Nonce storage uses ConcurrentHashMap with scheduled cleanup (TTL = 5 minutes).
 * Order: After RequestLog, before ApiVersion
 */
@Slf4j
@Component
public class UtmCallbackFilter implements GlobalFilter, Ordered {

    @Value("${gateway.utm.whitelist:}")
    private String whitelistStr;

    @Value("${gateway.utm.secret:}")
    private String utmSecret;

    @Value("${gateway.utm.replay-window:300}")
    private long replayWindowSeconds;

    /** Nonce 过期时间：5 分钟（毫秒） */
    private static final long NONCE_TTL_MS = 5 * 60 * 1000L;

    /** Nonce 清理间隔：1 分钟 */
    private static final long CLEANUP_INTERVAL_SECONDS = 60L;

    private static final String UTM_PATH_PREFIX = "/api/v1/utm/callback";
    private static final String SIGNATURE_HEADER = "X-UTM-Signature";
    private static final String TIMESTAMP_HEADER = "X-UTM-Timestamp";
    private static final String NONCE_HEADER = "X-UTM-Nonce";

    // Replay protection: store nonces with insertion timestamp, with scheduled cleanup
    private final Map<String, Long> usedNonces = new ConcurrentHashMap<>();

    private ScheduledExecutorService cleanupExecutor;

    @PostConstruct
    public void init() {
        cleanupExecutor = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "nonce-cleanup");
            t.setDaemon(true);
            return t;
        });
        cleanupExecutor.scheduleAtFixedRate(this::cleanupExpiredNonces,
                CLEANUP_INTERVAL_SECONDS, CLEANUP_INTERVAL_SECONDS, TimeUnit.SECONDS);
        log.info("[UTM] Nonce cleanup scheduler started, interval={}s, ttl={}ms",
                CLEANUP_INTERVAL_SECONDS, NONCE_TTL_MS);
    }

    @PreDestroy
    public void destroy() {
        if (cleanupExecutor != null) {
            cleanupExecutor.shutdown();
            try {
                if (!cleanupExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                    cleanupExecutor.shutdownNow();
                }
            } catch (InterruptedException e) {
                cleanupExecutor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    /**
     * 定期清理过期的 nonce，防止内存泄漏。
     */
    private void cleanupExpiredNonces() {
        long now = System.currentTimeMillis();
        int removed = 0;
        Iterator<Map.Entry<String, Long>> it = usedNonces.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<String, Long> entry = it.next();
            if (now - entry.getValue() > NONCE_TTL_MS) {
                it.remove();
                removed++;
            }
        }
        if (removed > 0) {
            log.debug("[UTM] Cleaned up {} expired nonces, remaining={}", removed, usedNonces.size());
        }
    }

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
        if (nonce == null || nonce.isEmpty() || usedNonces.containsKey(nonce)) {
            log.warn("[UTM] Invalid or reused nonce: id={}", requestId);
            return reject(exchange, HttpStatus.BAD_REQUEST, "Invalid or reused nonce");
        }

        // 4. HMAC Signature Verification
        String signature = request.getHeaders().getFirst(SIGNATURE_HEADER);
        String method = request.getMethod().name();
        String expectedSignature = generateHmac(method, path, timestampStr, nonce);

        if (signature == null || signature.isEmpty() || !signature.equals(expectedSignature)) {
            log.warn("[UTM] Invalid signature: id={}", requestId);
            return reject(exchange, HttpStatus.UNAUTHORIZED, "Invalid signature");
        }

        // Mark nonce as used (with timestamp for TTL cleanup)
        usedNonces.put(nonce, System.currentTimeMillis());
        log.info("[UTM] Callback validated successfully: id={}", requestId);

        return chain.filter(exchange);
    }

    private boolean isIpWhitelisted(String clientIp) {
        if (whitelistStr == null || whitelistStr.isEmpty()) {
            return true; // Allow all if no whitelist configured
        }
        List<String> whitelist = Arrays.asList(whitelistStr.split(","));
        return whitelist.stream().map(String::trim).anyMatch(entry -> matchIpOrCidr(entry, clientIp));
    }

    /**
     * 匹配 IP 地址或 CIDR 范围
     * 支持精确 IP 匹配（如 192.168.1.1）和 CIDR 表示法（如 10.0.0.0/8）
     */
    private boolean matchIpOrCidr(String whitelistEntry, String clientIp) {
        if (whitelistEntry.contains("/")) {
            return matchCidr(whitelistEntry, clientIp);
        }
        return whitelistEntry.equals(clientIp);
    }

    /**
     * CIDR 匹配：将白名单条目和客户端 IP 转换为字节数组进行前缀匹配
     */
    private boolean matchCidr(String cidr, String clientIp) {
        try {
            String[] parts = cidr.split("/");
            if (parts.length != 2) {
                log.warn("[UTM] Invalid CIDR format: {}", cidr);
                return false;
            }
            byte[] networkBytes = InetAddress.getByName(parts[0]).getAddress();
            int prefixLength = Integer.parseInt(parts[1]);
            byte[] clientBytes = InetAddress.getByName(clientIp).getAddress();

            if (networkBytes.length != clientBytes.length) {
                return false;
            }

            // 逐字节进行前缀匹配
            int fullBytes = prefixLength / 8;
            int remainingBits = prefixLength % 8;

            for (int i = 0; i < fullBytes; i++) {
                if (networkBytes[i] != clientBytes[i]) {
                    return false;
                }
            }

            if (remainingBits > 0 && fullBytes < networkBytes.length) {
                int mask = (0xFF << (8 - remainingBits)) & 0xFF;
                if ((networkBytes[fullBytes] & mask) != (clientBytes[fullBytes] & mask)) {
                    return false;
                }
            }

            return true;
        } catch (UnknownHostException e) {
            log.warn("[UTM] Failed to parse IP address for CIDR match: cidr={}, ip={}, error={}",
                    cidr, clientIp, e.getMessage());
            return false;
        } catch (NumberFormatException e) {
            log.warn("[UTM] Invalid CIDR prefix length: {}", cidr);
            return false;
        }
    }

    private boolean isValidTimestamp(String timestampStr) {
        if (timestampStr == null || timestampStr.isEmpty()) {
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
            var remoteAddress = request.getRemoteAddress();
            ip = remoteAddress != null
                    ? remoteAddress.getAddress().getHostAddress()
                    : "unknown";
        }
        return ip.split(",")[0].trim();
    }

    @SuppressWarnings("null")
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

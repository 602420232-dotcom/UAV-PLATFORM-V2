package com.uav.common.security.ratelimit;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.annotation.Order;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;
import java.util.List;

/**
 * 限流过滤器
 * <p>
 * 基于 Redis + Lua 脚本实现滑动窗口限流，支持三种限流维度：
 * <ul>
 *     <li>GLOBAL — 全局限流</li>
 *     <li>USER — 按用户ID限流</li>
 *     <li>API — 按 API 路径限流</li>
 * </ul>
 * <p>
 * Lua 脚本保证原子性：检查计数 -> 判断是否超限 -> 递增计数 -> 设置过期时间。
 * <p>
 * 过滤器顺序：在安全过滤器之前执行（Order=50），确保未认证请求也被限流。
 */
@Slf4j
@Component
@Order(50)
@RequiredArgsConstructor
public class RateLimitFilter extends OncePerRequestFilter {

    private final StringRedisTemplate redisTemplate;
    private final RateLimitProperties rateLimitProperties;

    /** 限流响应头：剩余请求数 */
    public static final String HEADER_X_RATE_LIMIT_REMAINING = "X-RateLimit-Remaining";
    /** 限流响应头：最大请求数 */
    public static final String HEADER_X_RATE_LIMIT_LIMIT = "X-RateLimit-Limit";
    /** 限流响应头：重试时间（秒） */
    public static final String HEADER_RETRY_AFTER = "Retry-After";

    /**
     * Redis Lua 限流脚本（滑动窗口）
     * <p>
     * KEYS[1] = 限流 key
     * ARGV[1] = 时间窗口（秒）
     * ARGV[2] = 最大请求数
     * <p>
     * 返回值：
     * -1 = 超出限流
     * >= 0 = 剩余配额
     */
    private static final String RATE_LIMIT_SCRIPT = """
            local key = KEYS[1]
            local window = tonumber(ARGV[1])
            local limit = tonumber(ARGV[2])
            local current = tonumber(redis.call('GET', key) or '0')
            if current >= limit then
                return -1
            end
            local remaining = redis.call('INCR', key)
            if remaining == 1 then
                redis.call('EXPIRE', key, window)
            end
            return limit - remaining
            """;

    private final DefaultRedisScript<Long> rateLimitRedisScript = new DefaultRedisScript<>() {{
        setScriptText(RATE_LIMIT_SCRIPT);
        setResultType(Long.class);
    }};

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        // 限流未启用，直接放行
        if (!rateLimitProperties.isEnabled()) {
            filterChain.doFilter(request, response);
            return;
        }

        String requestUri = request.getRequestURI();

        // 构建限流 key
        String limitKey = buildLimitKey(request);

        // 获取该路径的限流配置
        int maxRequests = rateLimitProperties.getMaxRequestsForPath(requestUri);
        int windowSeconds = rateLimitProperties.getDefaultWindowSeconds();

        // 执行 Redis Lua 限流脚本
        try {
            Long remaining = redisTemplate.execute(
                    rateLimitRedisScript,
                    Collections.singletonList(limitKey),
                    String.valueOf(windowSeconds),
                    String.valueOf(maxRequests)
            );

            if (remaining != null && remaining == -1) {
                // 超出限流
                log.warn("请求被限流 - uri: {}, key: {}", requestUri, limitKey);
                response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                response.setCharacterEncoding("UTF-8");
                response.setHeader(HEADER_RETRY_AFTER, String.valueOf(windowSeconds));
                response.setHeader(HEADER_X_RATE_LIMIT_LIMIT, String.valueOf(maxRequests));
                response.setHeader(HEADER_X_RATE_LIMIT_REMAINING, "0");
                String json = String.format(
                        "{\"code\":429,\"message\":\"请求过于频繁，请稍后再试\"}");
                response.getWriter().write(json);
                return;
            }

            // 设置限流响应头
            if (remaining != null) {
                response.setHeader(HEADER_X_RATE_LIMIT_LIMIT, String.valueOf(maxRequests));
                response.setHeader(HEADER_X_RATE_LIMIT_REMAINING, String.valueOf(remaining));
            }

        } catch (Exception e) {
            // Redis 异常时降级放行，避免影响业务可用性
            log.error("限流检查异常，降级放行 - uri: {}", requestUri, e);
        }

        filterChain.doFilter(request, response);
    }

    /**
     * 构建限流 Redis Key
     * <p>
     * Key 格式：{prefix}:{type}:{identifier}
     * <ul>
     *     <li>GLOBAL: uav:ratelimit:global:{uri}</li>
     *     <li>USER: uav:ratelimit:user:{userId}:{uri}</li>
     *     <li>API: uav:ratelimit:api:{uri}</li>
     * </ul>
     *
     * @param request HTTP 请求
     * @return Redis Key
     */
    private String buildLimitKey(HttpServletRequest request) {
        String prefix = rateLimitProperties.getKeyPrefix();
        String uri = request.getRequestURI();

        // 优先按用户限流，未认证则按 API 限流
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.isAuthenticated()
                && authentication.getPrincipal() instanceof com.uav.common.security.rbac.RbacUserDetails userDetails) {
            return String.format("%s:user:%d:%s", prefix, userDetails.getId(), uri);
        }

        return String.format("%s:api:%s", prefix, uri);
    }
}

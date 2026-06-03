package com.uav.common.resilience;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 轻量级本地限流服务
 * 
 * 当请求不经过 API 网关时，作为本地熔断降级方案。
 * 使用滑动窗口计数器算法，避免引入额外依赖。
 */
@Service
public class RateLimitService {

    private static final Logger log = LoggerFactory.getLogger(RateLimitService.class);
    private static final int DEFAULT_MAX_REQUESTS = 100;
    private static final long WINDOW_MS = 60_000L;

    private final Map<String, WindowCounter> counters = new ConcurrentHashMap<>();

    /**
     * 检查当前请求是否被限流
     *
     * @param maxRequests 窗口内最大请求数
     * @return true 如果请求被允许，false 如果被限流
     */
    public boolean tryAcquire(int maxRequests) {
        String key = resolveClientKey();
        WindowCounter counter = counters.computeIfAbsent(key, k -> new WindowCounter());
        return counter.tryAcquire(maxRequests);
    }

    /**
     * 使用默认阈值检查限流
     */
    public boolean tryAcquire() {
        return tryAcquire(DEFAULT_MAX_REQUESTS);
    }

    /**
     * 获取当前客户端已使用的请求数
     */
    public int getCurrentUsage() {
        String key = resolveClientKey();
        WindowCounter counter = counters.get(key);
        return counter != null ? counter.count.get() : 0;
    }

    private String resolveClientKey() {
        try {
            ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.currentRequestAttributes();
            HttpServletRequest request = attrs.getRequest();
            
            // 优先使用用户 ID
            String userId = request.getHeader("X-User-Id");
            if (userId != null) return "user:" + userId;
            
            // 降级为 IP
            String ip = request.getRemoteAddr();
            return "ip:" + (ip != null ? ip : "unknown");
        } catch (Exception e) {
            return "unknown:" + Thread.currentThread().getName();
        }
    }

    /**
     * 滑动窗口计数器
     */
    private static class WindowCounter {
        private final AtomicInteger count = new AtomicInteger(0);
        private volatile long windowStart = System.currentTimeMillis();

        boolean tryAcquire(int maxRequests) {
            long now = System.currentTimeMillis();
            
            // 如果窗口过期，重置
            if (now - windowStart > WINDOW_MS) {
                synchronized (this) {
                    if (now - windowStart > WINDOW_MS) {
                        count.set(0);
                        windowStart = now;
                    }
                }
            }

            int current = count.incrementAndGet();
            if (current > maxRequests) {
                count.decrementAndGet();
                log.warn("Rate limit exceeded: {} requests in window (max: {})", current - 1, maxRequests);
                return false;
            }
            
            return true;
        }
    }
}

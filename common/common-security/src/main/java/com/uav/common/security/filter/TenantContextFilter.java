package com.uav.common.security.filter;

import com.uav.common.core.util.TenantContext;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 租户上下文过滤器
 * <p>
 * 从请求 Header 中提取 tenantId、apiKey、requestId，存入 ThreadLocal 租户上下文。
 * 在所有安全过滤器之前执行，确保后续过滤器可以读取租户信息。
 * <p>
 * 过滤器顺序：最高优先级（最先执行）
 */
@Slf4j
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TenantContextFilter extends OncePerRequestFilter {

    public static final String HEADER_TENANT_ID = "X-Tenant-Id";
    public static final String HEADER_API_KEY = "X-Api-Key";
    public static final String HEADER_REQUEST_ID = "X-Request-Id";
    public static final String HEADER_EMERGENCY = "X-Emergency";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            String tenantId = request.getHeader(HEADER_TENANT_ID);
            String apiKey = request.getHeader(HEADER_API_KEY);
            String requestId = request.getHeader(HEADER_REQUEST_ID);
            String emergency = request.getHeader(HEADER_EMERGENCY);

            if (tenantId != null && !tenantId.isBlank()) {
                TenantContext.setTenantId(tenantId);
                log.debug("租户上下文设置 - tenantId: {}", tenantId);
            }

            if (apiKey != null && !apiKey.isBlank()) {
                TenantContext.setApiKey(apiKey);
                log.debug("租户上下文设置 - apiKey: {}", apiKey);
            }

            if (requestId != null && !requestId.isBlank()) {
                TenantContext.setRequestId(requestId);
            } else {
                // 若请求方未传 requestId，则生成一个
                TenantContext.setRequestId(java.util.UUID.randomUUID().toString().replace("-", ""));
            }

            if ("true".equalsIgnoreCase(emergency)) {
                TenantContext.setEmergency(true);
                log.warn("应急模式已激活 - tenantId: {}", tenantId);
            }

            filterChain.doFilter(request, response);
        } finally {
            // 请求结束后清理 ThreadLocal，防止内存泄漏
            TenantContext.clear();
            log.debug("租户上下文已清理");
        }
    }
}

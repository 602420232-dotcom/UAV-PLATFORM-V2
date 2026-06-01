package com.uav.common.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

public class CsrfOriginFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(CsrfOriginFilter.class);

    private final CookieCsrfTokenRepository.CsrfOriginValidator originValidator;
    private final boolean enabled;

    public CsrfOriginFilter(String allowedOrigin, boolean enabled) {
        this.originValidator = new CookieCsrfTokenRepository.CsrfOriginValidator(allowedOrigin);
        this.enabled = enabled;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        if (!enabled || isPublicPath(request.getRequestURI())) {
            filterChain.doFilter(request, response);
            return;
        }

        String method = request.getMethod();
        if ("GET".equals(method) || "HEAD".equals(method) || "OPTIONS".equals(method)) {
            filterChain.doFilter(request, response);
            return;
        }

        if (!originValidator.isValid(request)) {
            log.warn("CSRF检查失败: {} {} - Origin/Referer不匹配", method, request.getRequestURI());
            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"success\":false,\"error\":\"CSRF验证失败\"}");
            return;
        }

        filterChain.doFilter(request, response);
    }

    private boolean isPublicPath(String uri) {
        return uri.equals("/actuator/health") || uri.equals("/actuator/info")
                || uri.startsWith("/api/public/") || uri.startsWith("/api/auth/");
    }
}

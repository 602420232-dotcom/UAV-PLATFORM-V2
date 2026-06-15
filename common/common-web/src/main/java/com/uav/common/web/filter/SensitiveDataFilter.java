package com.uav.common.web.filter;

import com.uav.common.web.sensitive.SensitiveDataUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.util.ContentCachingRequestWrapper;
import org.springframework.web.util.ContentCachingResponseWrapper;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

/**
 * 敏感数据日志过滤器。
 * <p>
 * 拦截请求和响应，在日志输出时对敏感数据（手机号、邮箱、身份证号等）进行脱敏。
 * 使用 {@link ContentCachingRequestWrapper} 和 {@link ContentCachingResponseWrapper}
 * 缓存请求/响应体，以便在日志中记录脱敏后的内容。
 */
@Slf4j
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 20)
public class SensitiveDataFilter extends OncePerRequestFilter {

    /** 最大缓存的请求体大小（10KB），超出部分不缓存 */
    private static final int MAX_PAYLOAD_SIZE = 10 * 1024;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        // 仅对 JSON API 请求进行日志脱敏
        String contentType = request.getContentType();
        boolean isJsonRequest = contentType != null && contentType.contains("application/json");

        if (!isJsonRequest) {
            filterChain.doFilter(request, response);
            return;
        }

        ContentCachingRequestWrapper wrappedRequest = new ContentCachingRequestWrapper(request, MAX_PAYLOAD_SIZE);
        ContentCachingResponseWrapper wrappedResponse = new ContentCachingResponseWrapper(response);

        try {
            filterChain.doFilter(wrappedRequest, wrappedResponse);
        } finally {
            // 记录脱敏后的请求体
            byte[] requestBytes = wrappedRequest.getContentAsByteArray();
            if (requestBytes.length > 0 && requestBytes.length < MAX_PAYLOAD_SIZE) {
                String requestBody = new String(requestBytes, StandardCharsets.UTF_8);
                String desensitized = SensitiveDataUtil.desensitize(requestBody);
                log.debug("[SensitiveData] Request body (desensitized): {}", desensitized);
            }

            // 记录脱敏后的响应体
            byte[] responseBytes = wrappedResponse.getContentAsByteArray();
            if (responseBytes.length > 0 && responseBytes.length < MAX_PAYLOAD_SIZE) {
                String responseBody = new String(responseBytes, StandardCharsets.UTF_8);
                String desensitized = SensitiveDataUtil.desensitize(responseBody);
                log.debug("[SensitiveData] Response body (desensitized): {}", desensitized);
            }

            // 必须将缓存的响应体写回原始 response
            wrappedResponse.copyBodyToResponse();
        }
    }
}

package com.uav.common.security.filter;

import com.uav.common.core.util.HmacUtil;
import com.uav.common.core.util.TenantContext;
import com.uav.common.security.annotation.RequireApiKey;
import com.uav.common.security.service.ApiKeyService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerExecutionChain;
import org.springframework.web.servlet.HandlerMapping;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Scanner;

/**
 * HMAC 签名验证过滤器
 * <p>
 * 对标记了 {@link RequireApiKey} 的接口进行 HMAC-SHA256 签名验证。
 * 签名规则：method + path + timestamp + apiKey + body，使用 API Key 对应的 Secret 签名。
 * <p>
 * 过滤器顺序：在 TenantContextFilter 之后，JwtAuthenticationFilter 之前
 */
@Slf4j
@Component
@ConditionalOnBean(ApiKeyService.class)
@Order(100)
public class HmacAuthenticationFilter extends OncePerRequestFilter {

    public static final String HEADER_TIMESTAMP = "X-Timestamp";
    public static final String HEADER_SIGNATURE = "X-Signature";
    public static final String HEADER_API_KEY = "X-Api-Key";

    private final ApiKeyService apiKeyService;
    private final List<HandlerMapping> handlerMappings;

    public HmacAuthenticationFilter(ApiKeyService apiKeyService, List<HandlerMapping> handlerMappings) {
        this.apiKeyService = apiKeyService;
        this.handlerMappings = handlerMappings;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        // 仅对标记了 @RequireApiKey 的方法进行 HMAC 校验
        if (!requiresApiKey(request)) {
            filterChain.doFilter(request, response);
            return;
        }

        String apiKey = request.getHeader(HEADER_API_KEY);
        String timestamp = request.getHeader(HEADER_TIMESTAMP);
        String signature = request.getHeader(HEADER_SIGNATURE);

        if (apiKey == null || apiKey.isBlank()) {
            writeError(response, HttpStatus.UNAUTHORIZED, "缺少 API Key");
            return;
        }
        if (timestamp == null || timestamp.isBlank()) {
            writeError(response, HttpStatus.UNAUTHORIZED, "缺少时间戳");
            return;
        }
        if (signature == null || signature.isBlank()) {
            writeError(response, HttpStatus.UNAUTHORIZED, "缺少签名");
            return;
        }

        if (!apiKeyService.isValidApiKey(apiKey)) {
            writeError(response, HttpStatus.UNAUTHORIZED, "无效的 API Key");
            return;
        }

        String secret = apiKeyService.getSecretByApiKey(apiKey);
        if (secret == null || secret.isBlank()) {
            writeError(response, HttpStatus.UNAUTHORIZED, "未找到 API Key 对应的 Secret");
            return;
        }

        // 校验时间戳（5分钟有效期）
        try {
            long ts = Long.parseLong(timestamp);
            long now = System.currentTimeMillis();
            if (Math.abs(now - ts) > 5 * 60 * 1000) {
                writeError(response, HttpStatus.UNAUTHORIZED, "请求已过期，时间戳超出有效范围");
                return;
            }
        } catch (NumberFormatException e) {
            writeError(response, HttpStatus.UNAUTHORIZED, "时间戳格式错误");
            return;
        }

        // 读取请求体并构建签名字符串
        String body = readBody(request);
        String signString = HmacUtil.buildSignString(
                request.getMethod(),
                request.getRequestURI(),
                timestamp,
                apiKey,
                body
        );

        if (!HmacUtil.verify(signString, secret, signature)) {
            log.warn("HMAC 签名验证失败 - apiKey: {}, uri: {}", apiKey, request.getRequestURI());
            writeError(response, HttpStatus.UNAUTHORIZED, "签名验证失败");
            return;
        }

        log.debug("HMAC 签名验证通过 - apiKey: {}, uri: {}", apiKey, request.getRequestURI());
        filterChain.doFilter(request, response);
    }

    /**
     * 判断当前请求是否标记了 @RequireApiKey
     */
    private boolean requiresApiKey(HttpServletRequest request) {
        try {
            for (HandlerMapping handlerMapping : handlerMappings) {
                HandlerExecutionChain handlerChain = handlerMapping.getHandler(request);
                if (handlerChain != null) {
                    Object handler = handlerChain.getHandler();
                    if (handler instanceof HandlerMethod handlerMethod) {
                        return handlerMethod.hasMethodAnnotation(RequireApiKey.class);
                    }
                }
            }
        } catch (Exception e) {
            log.warn("判断 @RequireApiKey 时发生异常", e);
        }
        return false;
    }

    /**
     * 读取请求体内容
     */
    private String readBody(HttpServletRequest request) {
        try (Scanner scanner = new Scanner(request.getInputStream(), StandardCharsets.UTF_8)) {
            scanner.useDelimiter("\\A");
            return scanner.hasNext() ? scanner.next() : "";
        } catch (IOException e) {
            log.warn("读取请求体失败", e);
            return "";
        }
    }

    /**
     * 写入错误响应
     */
    private void writeError(HttpServletResponse response, HttpStatus status, String message) throws IOException {
        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        String json = String.format("{\"code\":%d,\"message\":\"%s\"}", status.value(), message);
        response.getWriter().write(json);
    }
}

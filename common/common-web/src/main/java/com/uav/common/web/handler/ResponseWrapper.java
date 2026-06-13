package com.uav.common.web.handler;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.context.MockContext;
import com.uav.common.core.result.Result;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.MethodParameter;
import org.springframework.http.MediaType;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;

/**
 * 响应包装器：自动将Controller返回值包装为Result
 * <p>
 * 同时检测 MockContext 标记，若当前请求使用了 Mock 数据，
 * 则在响应头中添加 X-Mock: true。
 */
@Slf4j
@RequiredArgsConstructor
@RestControllerAdvice(basePackages = "com.uav")
public class ResponseWrapper implements ResponseBodyAdvice<Object> {

    private final ObjectMapper objectMapper;

    @Override
    public boolean supports(MethodParameter returnType,
                            Class<? extends HttpMessageConverter<?>> converterType) {
        return true;
    }

    @Override
    @SuppressWarnings("unchecked")
    public Object beforeBodyWrite(Object body,
                                  MethodParameter returnType,
                                  MediaType selectedContentType,
                                  Class<? extends HttpMessageConverter<?>> selectedConverterType,
                                  ServerHttpRequest request,
                                  ServerHttpResponse response) {
        // 检查 Mock 标记并添加响应头
        if (MockContext.isMockMode()) {
            response.getHeaders().add(MockContext.MOCK_HEADER_NAME, MockContext.MOCK_HEADER_VALUE);
            MockContext.clear();
        }

        if (body instanceof Result) {
            return body;
        }

        if (body instanceof String) {
            try {
                response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
                return objectMapper.writeValueAsString(Result.success(body));
            } catch (JsonProcessingException e) {
                log.error("响应包装失败", e);
                return body;
            }
        }

        return Result.success(body);
    }
}

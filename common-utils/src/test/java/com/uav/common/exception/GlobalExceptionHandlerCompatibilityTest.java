package com.uav.common.exception;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("GlobalExceptionHandler 异常处理")
class GlobalExceptionHandlerCompatibilityTest {

    private final com.uav.common.exception.GlobalExceptionHandler handler =
            new com.uav.common.exception.GlobalExceptionHandler();

    @Nested
    @DisplayName("common-utils 基础处理器")
    class CommonUtilsHandler {

        @Test
    @DisplayName("处理 IllegalArgumentException → 400")
    void shouldHandleIllegalArgument() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleIllegalArgument(new IllegalArgumentException("test error"));
        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        Map<String, Object> body = response.getBody();
        assertNotNull(body);
        assertEquals("参数错误", body.get("error"));
    }

    @Test
    @DisplayName("处理 AccessDeniedException → 403")
    void shouldHandleAccessDenied() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleAccessDenied(new org.springframework.security.access.AccessDeniedException("权限不足"));
        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
    }

    @Test
    @DisplayName("处理 PythonExecutionException → 500")
    void shouldHandlePythonError() {
        PythonExecutionException ex = new PythonExecutionException("test_script.py", "error detail");
        ResponseEntity<Map<String, Object>> response = handler.handlePythonError(ex);
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        Map<String, Object> body = response.getBody();
        assertNotNull(body);
        assertTrue(body.containsKey("script"));
    }

    @Test
    @DisplayName("处理 ServiceUnavailableException → 503")
    void shouldHandleServiceUnavailable() {
        ServiceUnavailableException ex = new ServiceUnavailableException("test-service", "服务暂时不可用", HttpStatus.SERVICE_UNAVAILABLE);
        ResponseEntity<Map<String, Object>> response = handler.handleServiceUnavailable(ex);
        assertTrue(response.getStatusCode().is5xxServerError());
    }

    @Test
    @DisplayName("处理 ResourceAccessException with ConnectException → 503")
    void shouldHandleConnectException() {
        org.springframework.web.client.ResourceAccessException ex =
            new org.springframework.web.client.ResourceAccessException("connect error", new java.net.ConnectException("refused"));
        ResponseEntity<Map<String, Object>> response = handler.handleResourceAccess(ex);
        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode());
    }

    @Test
    @DisplayName("处理 ResourceAccessException with SocketTimeoutException → 504")
    void shouldHandleSocketTimeout() {
        org.springframework.web.client.ResourceAccessException ex =
            new org.springframework.web.client.ResourceAccessException("timeout", new java.net.SocketTimeoutException("timeout"));
        ResponseEntity<Map<String, Object>> response = handler.handleResourceAccess(ex);
        assertEquals(HttpStatus.GATEWAY_TIMEOUT, response.getStatusCode());
    }

    @Test
    @DisplayName("处理 RestClientException → 502")
    void shouldHandleRestClientError() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleRestClientError(new org.springframework.web.client.RestClientException("bad gateway"));
        assertEquals(HttpStatus.BAD_GATEWAY, response.getStatusCode());
    }

    @Test
    @DisplayName("处理 BusinessException → 对应HTTP状态码")
    void shouldHandleBusinessError() {
        BusinessException ex = new BusinessException("BIZ_001", "业务错误", HttpStatus.CONFLICT);
        ResponseEntity<Map<String, Object>> response = handler.handleBusinessError(ex);
        assertEquals(HttpStatus.CONFLICT, response.getStatusCode());
        Map<String, Object> body = response.getBody();
        assertNotNull(body);
        assertEquals("BIZ_001", body.get("code"));
    }

    @Test
    @DisplayName("处理 DataNotFoundException → 404")
    void shouldHandleDataNotFound() {
        DataNotFoundException ex = new DataNotFoundException("Drone", (Object)"123");
        ResponseEntity<Map<String, Object>> response = handler.handleDataNotFound(ex);
        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        Map<String, Object> body = response.getBody();
        assertNotNull(body);
        assertEquals("数据不存在", body.get("error"));
    }

    @Test
    @DisplayName("处理 TimeoutException → 504")
    void shouldHandleTimeout() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleTimeout(new java.util.concurrent.TimeoutException("timeout"));
        assertEquals(HttpStatus.GATEWAY_TIMEOUT, response.getStatusCode());
    }

    @Test
    @DisplayName("处理 InterruptedException → 500")
    void shouldHandleInterrupted() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleInterrupted(new java.lang.InterruptedException());
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertTrue(Thread.interrupted());
    }

    @Test
    @DisplayName("处理通用 Exception → 500")
    void shouldHandleGenericException() {
        ResponseEntity<Map<String, Object>> response =
                handler.handleException(new RuntimeException("unknown error"));
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        Map<String, Object> body = response.getBody();
        assertNotNull(body);
        assertEquals("服务器内部错误", body.get("error"));
    }
    }
}
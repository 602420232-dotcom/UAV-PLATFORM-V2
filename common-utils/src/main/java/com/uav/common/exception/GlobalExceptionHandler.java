package com.uav.common.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.servlet.NoHandlerFoundException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.ResourceAccessException;
import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeoutException;
import java.util.stream.Collectors;

@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalArgument(IllegalArgumentException e) {
        log.warn("参数错误: {}", e.getMessage());
        return buildError(HttpStatus.BAD_REQUEST, "参数错误", e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException e) {
        String errors = e.getBindingResult().getFieldErrors().stream()
                .map(f -> f.getField() + ": " + f.getDefaultMessage())
                .collect(Collectors.joining("; "));
        log.warn("参数校验失败: {}", errors);
        return buildError(HttpStatus.BAD_REQUEST, "参数校验失败", errors);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Map<String, Object>> handleAccessDenied(AccessDeniedException e) {
        log.warn("权限不足: {}", e.getMessage());
        return buildError(HttpStatus.FORBIDDEN, "权限不足", null);
    }

    @ExceptionHandler(NoHandlerFoundException.class)
    public ResponseEntity<Map<String, Object>> handleNotFound(NoHandlerFoundException e) {
        log.warn("资源不存在: {}", e.getRequestURL());
        return buildError(HttpStatus.NOT_FOUND, "资源不存在", null);
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<Map<String, Object>> handleMethodNotAllowed(HttpRequestMethodNotSupportedException e) {
        log.warn("请求方法不允许: {}", e.getMethod());
        return buildError(HttpStatus.METHOD_NOT_ALLOWED, "请求方法不允许", null);
    }

    @ExceptionHandler(PythonExecutionException.class)
    public ResponseEntity<Map<String, Object>> handlePythonError(PythonExecutionException e) {
        log.error("Python脚本执行失败: {} - {}", e.getScriptName(), e.getMessage(), e);
        return buildError(HttpStatus.INTERNAL_SERVER_ERROR, "算法处理失败", Map.of("script", e.getScriptName()));
    }

    @ExceptionHandler(ServiceUnavailableException.class)
    public ResponseEntity<Map<String, Object>> handleServiceUnavailable(ServiceUnavailableException e) {
        log.error("服务不可用: {} ({})", e.getServiceName(), e.getMessage());
        HttpStatusCode statusCode = e.getHttpStatus();
        return ResponseEntity.status(statusCode != null ? statusCode : HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("code", statusCode != null ? statusCode.value() : 500,
                        "message", "服务暂时不可用: " + e.getServiceName()));
    }

    @ExceptionHandler(ResourceAccessException.class)
    public ResponseEntity<Map<String, Object>> handleResourceAccess(ResourceAccessException e) {
        log.error("资源访问失败: {}", e.getMessage());
        Throwable cause = e.getCause();
        if (cause instanceof ConnectException) {
            return buildError(HttpStatus.SERVICE_UNAVAILABLE, "无法连接到远程服务", null);
        }
        if (cause instanceof SocketTimeoutException) {
            return buildError(HttpStatus.GATEWAY_TIMEOUT, "服务响应超时", null);
        }
        return buildError(HttpStatus.SERVICE_UNAVAILABLE, "资源访问失败", null);
    }

    @ExceptionHandler(RestClientException.class)
    public ResponseEntity<Map<String, Object>> handleRestClientError(RestClientException e) {
        log.error("REST客户端错误: {}", e.getMessage());
        return buildError(HttpStatus.BAD_GATEWAY, "服务调用失败", null);
    }

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Map<String, Object>> handleBusinessError(BusinessException e) {
        log.warn("业务异常: {} ({})", e.getCode(), e.getMessage());
        HttpStatusCode statusCode = e.getHttpStatus();
        return ResponseEntity.status(statusCode != null ? statusCode : HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("code", statusCode != null ? statusCode.value() : 500,
                        "message", e.getMessage()));
    }

    @ExceptionHandler(DataNotFoundException.class)
    public ResponseEntity<Map<String, Object>> handleDataNotFound(DataNotFoundException e) {
        log.warn("数据不存在: {} (id={})", e.getEntity(), e.getId());
        return buildError(HttpStatus.NOT_FOUND, e.getEntity() + " 不存在", null);
    }

    @ExceptionHandler(TimeoutException.class)
    public ResponseEntity<Map<String, Object>> handleTimeout(TimeoutException e) {
        log.error("操作超时: {}", e.getMessage());
        return buildError(HttpStatus.GATEWAY_TIMEOUT, "操作超时，请稍后重试", null);
    }

    @ExceptionHandler(InterruptedException.class)
    public ResponseEntity<Map<String, Object>> handleInterrupted(InterruptedException e) {
        Thread.currentThread().interrupt();
        log.error("操作被中断", e);
        return buildError(HttpStatus.INTERNAL_SERVER_ERROR, "操作被中断", null);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleException(Exception e) {
        log.error("服务器内部错误: {}", e.getMessage(), e);
        return buildError(HttpStatus.INTERNAL_SERVER_ERROR, "服务器内部错误", null);
    }

    private ResponseEntity<Map<String, Object>> buildError(HttpStatus status, String message, Object detail) {
        Map<String, Object> body = new HashMap<>();
        body.put("code", status.value());
        body.put("message", message);
        if (detail != null) {
            body.put("data", detail instanceof String ? Map.of("detail", detail) : detail);
        }
        return ResponseEntity.status(status).body(body);
    }
}

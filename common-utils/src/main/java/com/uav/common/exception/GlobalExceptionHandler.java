package com.uav.common.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.NoHandlerFoundException;
import org.springframework.web.HttpRequestMethodNotSupportedException;

import java.util.HashMap;
import java.util.Map;

/**
 * 通用全局异常处理器
 *
 * 各服务无需重复定义，此处理器会自动被所有扫描到 com.uav 包的服务加载。
 * 如需自定义异常处理，请使用组合模式（委托）而非继承：
 * <pre>
 * &#64;RestControllerAdvice
 * public class MyExceptionHandler {
 *     private final GlobalExceptionHandler delegate = new GlobalExceptionHandler();
 *
 *     &#64;ExceptionHandler(MyException.class)
 *     public ResponseEntity&lt;Map&lt;String, Object&gt;&gt; handleMyError(MyException e) {
 *         return delegate.buildError(HttpStatus.BAD_REQUEST, e.getMessage(), null);
 *     }
 * }
 * </pre>
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    protected ResponseEntity<Map<String, Object>> buildError(HttpStatus status, String message, Object detail) {
        Map<String, Object> body = new HashMap<>();
        body.put("code", status.value());
        body.put("message", message);
        if (detail != null) {
            body.put("data", detail instanceof String ? Map.of("detail", detail) : detail);
        }
        return ResponseEntity.status(status).body(body);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleAllExceptions(Exception ex, WebRequest request) {
        log.error("Request processing exception: {} - {}", 
            request != null ? request.getDescription(false) : "unknown", 
            ex.getMessage(), ex);
        return buildError(HttpStatus.INTERNAL_SERVER_ERROR, "服务器内部错误", null);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalArgument(IllegalArgumentException e) {
        log.warn("参数错误: {}", e.getMessage());
        return buildError(HttpStatus.BAD_REQUEST, "参数错误", e.getMessage());
    }

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Map<String, Object>> handleBusinessError(BusinessException e) {
        log.warn("业务异常: {} ({})", e.getCode(), e.getMessage());
        return buildError(e.getHttpStatus() != null ? e.getHttpStatus() : HttpStatus.INTERNAL_SERVER_ERROR, 
            e.getMessage(), null);
    }

    @ExceptionHandler(DataNotFoundException.class)
    public ResponseEntity<Map<String, Object>> handleDataNotFound(DataNotFoundException e) {
        log.warn("数据不存在: {} (id={})", e.getEntity(), e.getId());
        return buildError(HttpStatus.NOT_FOUND, e.getEntity() + " 不存在", null);
    }

    @ExceptionHandler(PythonExecutionException.class)
    public ResponseEntity<Map<String, Object>> handlePythonError(PythonExecutionException e) {
        log.error("Python脚本执行失败: {} - {}", e.getScriptName(), e.getMessage(), e);
        return buildError(HttpStatus.INTERNAL_SERVER_ERROR, "算法处理失败", 
            Map.of("script", e.getScriptName()));
    }

    @ExceptionHandler(ServiceUnavailableException.class)
    public ResponseEntity<Map<String, Object>> handleServiceUnavailable(ServiceUnavailableException e) {
        log.error("服务不可用: {} ({})", e.getServiceName(), e.getMessage());
        return buildError(e.getHttpStatus() != null ? e.getHttpStatus() : HttpStatus.SERVICE_UNAVAILABLE, 
            "服务暂时不可用: " + e.getServiceName(), null);
    }

    @ExceptionHandler(NoHandlerFoundException.class)
    public ResponseEntity<Map<String, Object>> handleNotFound(NoHandlerFoundException e) {
        log.warn("接口不存在: {}", e.getRequestURL());
        return buildError(HttpStatus.NOT_FOUND, "接口不存在", null);
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<Map<String, Object>> handleMethodNotAllowed(HttpRequestMethodNotSupportedException e) {
        log.warn("请求方法不允许: {} {}", e.getMethod(), e.getMessage());
        return buildError(HttpStatus.METHOD_NOT_ALLOWED, "请求方法不允许", null);
    }

    @ExceptionHandler(org.springframework.security.access.AccessDeniedException.class)
    public ResponseEntity<Map<String, Object>> handleAccessDenied(org.springframework.security.access.AccessDeniedException e) {
        log.warn("访问被拒绝: {}", e.getMessage());
        return buildError(HttpStatus.FORBIDDEN, "权限不足", null);
    }

    @ExceptionHandler(org.springframework.web.client.ResourceAccessException.class)
    public ResponseEntity<Map<String, Object>> handleResourceAccess(org.springframework.web.client.ResourceAccessException e) {
        if (e.getCause() instanceof java.net.ConnectException) {
            return buildError(HttpStatus.SERVICE_UNAVAILABLE, "服务连接失败", null);
        }
        if (e.getCause() instanceof java.net.SocketTimeoutException) {
            return buildError(HttpStatus.GATEWAY_TIMEOUT, "服务超时", null);
        }
        return buildError(HttpStatus.SERVICE_UNAVAILABLE, "服务访问异常", null);
    }

    @ExceptionHandler(org.springframework.web.client.RestClientException.class)
    public ResponseEntity<Map<String, Object>> handleRestClientError(org.springframework.web.client.RestClientException e) {
        log.error("REST 客户端异常: {}", e.getMessage());
        return buildError(HttpStatus.BAD_GATEWAY, "上游服务响应异常", null);
    }

    @ExceptionHandler(java.util.concurrent.TimeoutException.class)
    public ResponseEntity<Map<String, Object>> handleTimeout(java.util.concurrent.TimeoutException e) {
        log.error("处理超时: {}", e.getMessage());
        return buildError(HttpStatus.GATEWAY_TIMEOUT, "处理超时", null);
    }

    @ExceptionHandler(java.lang.InterruptedException.class)
    public ResponseEntity<Map<String, Object>> handleInterrupted(java.lang.InterruptedException e) {
        log.error("处理被中断");
        Thread.currentThread().interrupt();
        return buildError(HttpStatus.INTERNAL_SERVER_ERROR, "处理被中断", null);
    }

    @ExceptionHandler(java.lang.RuntimeException.class)
    public ResponseEntity<Map<String, Object>> handleException(java.lang.RuntimeException e) {
        log.error("运行时异常: {}", e.getMessage(), e);
        return buildError(HttpStatus.INTERNAL_SERVER_ERROR, "服务器内部错误", null);
    }
}

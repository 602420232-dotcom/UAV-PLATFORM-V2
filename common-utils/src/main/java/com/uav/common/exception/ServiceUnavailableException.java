package com.uav.common.exception;

import org.springframework.http.HttpStatus;

/**
 * 服务不可用异常
 * 用于标识下游服务调用失败（被熔断器保护）
 */
public class ServiceUnavailableException extends RuntimeException {
    private final String serviceName;
    private final HttpStatus httpStatus;

    /**
     * 默认构造函数，使用503 SERVICE_UNAVAILABLE
     */
    public ServiceUnavailableException(String serviceName, String message) {
        super(message);
        this.serviceName = serviceName;
        this.httpStatus = HttpStatus.SERVICE_UNAVAILABLE;
    }

    /**
     * 带HTTP状态码的构造函数
     */
    public ServiceUnavailableException(String serviceName, String message, HttpStatus httpStatus) {
        super(message);
        this.serviceName = serviceName;
        this.httpStatus = httpStatus != null ? httpStatus : HttpStatus.SERVICE_UNAVAILABLE;
    }

    /**
     * 带原因的构造函数
     */
    public ServiceUnavailableException(String serviceName, String message, Throwable cause) {
        super(message, cause);
        this.serviceName = serviceName;
        this.httpStatus = HttpStatus.SERVICE_UNAVAILABLE;
    }

    public String getServiceName() {
        return serviceName;
    }

    public HttpStatus getHttpStatus() {
        return httpStatus;
    }

    // ==================== 工厂方法 ====================

    /**
     * 创建503错误（服务不可用）
     */
    public static ServiceUnavailableException serviceDown(String serviceName, String message) {
        return new ServiceUnavailableException(serviceName, message, HttpStatus.SERVICE_UNAVAILABLE);
    }

    /**
     * 创建504错误（网关超时）
     */
    public static ServiceUnavailableException gatewayTimeout(String serviceName, String message) {
        return new ServiceUnavailableException(serviceName, message, HttpStatus.GATEWAY_TIMEOUT);
    }

    /**
     * 创建502错误（网关错误）
     */
    public static ServiceUnavailableException badGateway(String serviceName, String message) {
        return new ServiceUnavailableException(serviceName, message, HttpStatus.BAD_GATEWAY);
    }

    /**
     * 创建熔断器打开异常
     */
    public static ServiceUnavailableException circuitBreakerOpen(String serviceName) {
        return new ServiceUnavailableException(
                serviceName,
                "服务 " + serviceName + " 熔断器已打开，暂时不可用",
                HttpStatus.SERVICE_UNAVAILABLE
        );
    }
}

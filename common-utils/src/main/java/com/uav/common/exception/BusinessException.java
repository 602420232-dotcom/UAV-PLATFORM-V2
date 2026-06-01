package com.uav.common.exception;

import org.springframework.http.HttpStatus;

/**
 * 业务异常
 * 支持自定义HTTP状态码，便于区分不同类型的业务错误
 */
public class BusinessException extends RuntimeException {
    private final String code;
    private final HttpStatus httpStatus;

    /**
     * 默认构造函数，使用400 BAD_REQUEST状态码
     */
    public BusinessException(String code, String message) {
        super(message);
        this.code = code;
        this.httpStatus = HttpStatus.BAD_REQUEST;
    }

    /**
     * 带HTTP状态码的构造函数
     */
    public BusinessException(String code, String message, HttpStatus httpStatus) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus != null ? httpStatus : HttpStatus.BAD_REQUEST;
    }

    /**
     * 带原因的构造函数
     */
    public BusinessException(String code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
        this.httpStatus = HttpStatus.BAD_REQUEST;
    }

    /**
     * 带原因和HTTP状态码的构造函数
     */
    public BusinessException(String code, String message, Throwable cause, HttpStatus httpStatus) {
        super(message, cause);
        this.code = code;
        this.httpStatus = httpStatus != null ? httpStatus : HttpStatus.BAD_REQUEST;
    }

    public String getCode() {
        return code;
    }

    public HttpStatus getHttpStatus() {
        return httpStatus;
    }

    // ==================== 常用业务异常工厂方法 ====================

    /**
     * 创建400错误（参数错误）
     */
    public static BusinessException badRequest(String code, String message) {
        return new BusinessException(code, message, HttpStatus.BAD_REQUEST);
    }

    /**
     * 创建401错误（未认证）
     */
    public static BusinessException unauthorized(String code, String message) {
        return new BusinessException(code, message, HttpStatus.UNAUTHORIZED);
    }

    /**
     * 创建403错误（权限不足）
     */
    public static BusinessException forbidden(String code, String message) {
        return new BusinessException(code, message, HttpStatus.FORBIDDEN);
    }

    /**
     * 创建404错误（资源不存在）
     */
    public static BusinessException notFound(String code, String message) {
        return new BusinessException(code, message, HttpStatus.NOT_FOUND);
    }

    /**
     * 创建409错误（资源冲突）
     */
    public static BusinessException conflict(String code, String message) {
        return new BusinessException(code, message, HttpStatus.CONFLICT);
    }

    /**
     * 创建422错误（无法处理的实体）
     */
    public static BusinessException unprocessableEntity(String code, String message) {
        return new BusinessException(code, message, HttpStatus.UNPROCESSABLE_ENTITY);
    }

    /**
     * 创建429错误（请求过多）
     */
    public static BusinessException tooManyRequests(String code, String message) {
        return new BusinessException(code, message, HttpStatus.TOO_MANY_REQUESTS);
    }

    /**
     * 创建500错误（服务器内部错误）
     */
    public static BusinessException internal(String code, String message) {
        return new BusinessException(code, message, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}

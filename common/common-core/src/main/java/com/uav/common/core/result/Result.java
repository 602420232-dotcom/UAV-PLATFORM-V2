package com.uav.common.core.result;

import lombok.Data;

import java.io.Serializable;
import java.time.Instant;

/**
 * 统一API响应结构
 *
 * @param <T> 数据类型
 */
@Data
public class Result<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 业务状态码 */
    private int code;

    /** 提示消息 */
    private String message;

    /** 响应数据 */
    private T data;

    /** 请求追踪ID */
    private String requestId;

    /** 时间戳 */
    private long timestamp;

    public Result() {
        this.timestamp = Instant.now().toEpochMilli();
    }

    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode(ResultCode.SUCCESS.getCode());
        result.setMessage(ResultCode.SUCCESS.getMessage());
        result.setData(data);
        return result;
    }

    public static <T> Result<T> success() {
        return success(null);
    }

    public static <T> Result<T> error(int code, String message) {
        Result<T> result = new Result<>();
        result.setCode(code);
        result.setMessage(message);
        return result;
    }

    public static <T> Result<T> error(ResultCode resultCode) {
        return error(resultCode.getCode(), resultCode.getMessage());
    }

    public static <T> Result<T> error(ResultCode resultCode, String message) {
        return error(resultCode.getCode(), message);
    }

    public boolean isSuccess() {
        return this.code == ResultCode.SUCCESS.getCode();
    }
}

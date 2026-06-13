package com.uav.common.core.result;

import lombok.Getter;

/**
 * 统一业务状态码
 */
@Getter
public enum ResultCode {

    // 成功
    SUCCESS(200, "success"),

    // 客户端错误 1xxx
    BAD_REQUEST(1000, "请求参数错误"),
    UNAUTHORIZED(1001, "未授权，请先登录"),
    FORBIDDEN(1002, "权限不足"),
    NOT_FOUND(1003, "资源不存在"),
    METHOD_NOT_ALLOWED(1004, "请求方法不允许"),
    REQUEST_TIMEOUT(1005, "请求超时"),
    TOO_MANY_REQUESTS(1006, "请求过于频繁，请稍后重试"),
    API_KEY_INVALID(1007, "API Key无效或已过期"),
    HMAC_SIGNATURE_INVALID(1008, "HMAC签名验证失败"),
    TENANT_NOT_FOUND(1009, "租户不存在或已禁用"),
    API_VERSION_UNSUPPORTED(1010, "不支持的API版本"),

    // 服务端错误 2xxx
    INTERNAL_ERROR(2000, "服务器内部错误"),
    SERVICE_UNAVAILABLE(2001, "服务暂不可用"),
    EXTERNAL_SERVICE_ERROR(2002, "外部服务调用失败"),

    // 业务错误 3xxx
    TASK_NOT_FOUND(3000, "任务不存在"),
    TASK_ALREADY_EXISTS(3001, "任务已存在"),
    TASK_CANCELLED(3002, "任务已取消"),
    TASK_TIMEOUT(3003, "任务执行超时"),
    TASK_FAILED(3004, "任务执行失败"),
    ALGORITHM_NOT_FOUND(3005, "算法不存在"),
    ALGORITHM_NOT_SUPPORTED(3006, "当前场景不支持该算法"),
    AIRSPACE_REQUEST_FAILED(3007, "空域申请失败"),
    CONFLICT_DETECTED(3008, "检测到飞行冲突"),
    WEATHER_DATA_UNAVAILABLE(3009, "气象数据不可用"),
    ASSIMILATION_FAILED(3010, "数据同化失败"),
    PLANNING_FAILED(3011, "路径规划失败"),

    // 异步任务状态 1xx（与TaskStatus对齐）
    TASK_QUEUED(100, "排队中"),
    TASK_RUNNING(200, "运行中");

    private final int code;
    private final String message;

    ResultCode(int code, String message) {
        this.code = code;
        this.message = message;
    }
}

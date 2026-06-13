package com.uav.common.core.constant;

/**
 * 公共常量
 */
public final class CommonConstant {

    private CommonConstant() {}

    /** 请求头：租户ID */
    public static final String HEADER_TENANT_ID = "X-Tenant-Id";

    /** 请求头：API Key */
    public static final String HEADER_API_KEY = "X-API-Key";

    /** 请求头：API版本 */
    public static final String HEADER_API_VERSION = "X-API-Version";

    /** 请求头：请求追踪ID */
    public static final String HEADER_REQUEST_ID = "X-Request-Id";

    /** 请求头：HMAC时间戳 */
    public static final String HEADER_HMAC_TIMESTAMP = "X-HMAC-Timestamp";

    /** 请求头：HMAC签名 */
    public static final String HEADER_HMAC_SIGNATURE = "X-HMAC-Signature";

    /** 请求头：应急级别 */
    public static final String HEADER_EMERGENCY_LEVEL = "X-Emergency-Level";

    /** 默认分页大小 */
    public static final int DEFAULT_PAGE_SIZE = 20;

    /** 最大分页大小 */
    public static final int MAX_PAGE_SIZE = 1000;

    /** 默认时区 */
    public static final String DEFAULT_TIMEZONE = "Asia/Shanghai";

    /** 任务Redis Key前缀 */
    public static final String REDIS_TASK_PREFIX = "task:%s:%s";

    /** UTM nonce Redis Key前缀 */
    public static final String REDIS_UTM_NONCE_PREFIX = "utm:nonce:";

    /** 租户Schema前缀 */
    public static final String TENANT_SCHEMA_PREFIX = "tenant_";
}

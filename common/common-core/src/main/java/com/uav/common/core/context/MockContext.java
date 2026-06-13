package com.uav.common.core.context;

import org.slf4j.MDC;

/**
 * Mock 模式上下文
 * <p>
 * 用于标记当前请求是否使用了 Mock 数据。
 * Service 层在返回 Mock 数据前调用 {@link #setMockMode()}，
 * ResponseWrapper 在响应时读取该标记并添加 X-Mock Header。
 */
public class MockContext {

    private static final String MOCK_FLAG_KEY = "uav.mock.flag";
    public static final String MOCK_HEADER_NAME = "X-Mock";
    public static final String MOCK_HEADER_VALUE = "true";

    /**
     * 标记当前请求使用了 Mock 数据
     */
    public static void setMockMode() {
        MDC.put(MOCK_FLAG_KEY, MOCK_HEADER_VALUE);
    }

    /**
     * 清除 Mock 标记
     */
    public static void clear() {
        MDC.remove(MOCK_FLAG_KEY);
    }

    /**
     * 检查当前请求是否使用了 Mock 数据
     */
    public static boolean isMockMode() {
        return MOCK_HEADER_VALUE.equals(MDC.get(MOCK_FLAG_KEY));
    }
}

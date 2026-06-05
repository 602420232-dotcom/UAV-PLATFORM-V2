package com.uav.common.filter;

import org.slf4j.MDC;

import java.util.UUID;

/**
 * 日志追踪ID过滤器核心逻辑（不实现servlet接口，避免Reactive环境加载问题）
 * 
 * 在Servlet环境下，由 TraceIdFilterRegistration 自动注册为Servlet Filter。
 * Reactive环境（如API Gateway）不受影响。
 */
public class TraceIdFilter {

    private static final String TRACE_ID_HEADER = "X-Trace-Id";
    private static final String TRACE_ID_MDC_KEY = "traceId";

    public String getTraceIdHeader() {
        return TRACE_ID_HEADER;
    }

    public String getTraceIdMdcKey() {
        return TRACE_ID_MDC_KEY;
    }

    /**
     * 从请求头获取或生成traceId
     */
    public String resolveTraceId(String existingTraceId) {
        if (existingTraceId != null && !existingTraceId.isEmpty()) {
            return existingTraceId;
        }
        return UUID.randomUUID().toString().replace("-", "").substring(0, 16);
    }

    /**
     * 设置MDC上下文
     */
    public void setupMdc(String traceId) {
        MDC.put(TRACE_ID_MDC_KEY, traceId);
    }

    /**
     * 清理MDC上下文
     */
    public void cleanup() {
        MDC.remove(TRACE_ID_MDC_KEY);
    }
}

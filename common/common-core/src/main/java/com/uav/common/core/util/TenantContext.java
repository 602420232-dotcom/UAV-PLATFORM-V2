package com.uav.common.core.util;

/**
 * 租户上下文（ThreadLocal）
 */
public final class TenantContext {

    private TenantContext() {}

    private static final ThreadLocal<String> TENANT_ID = new ThreadLocal<>();
    private static final ThreadLocal<String> API_KEY = new ThreadLocal<>();
    private static final ThreadLocal<String> REQUEST_ID = new ThreadLocal<>();
    private static final ThreadLocal<Boolean> EMERGENCY = ThreadLocal.withInitial(() -> false);

    public static void setTenantId(String tenantId) {
        TENANT_ID.set(tenantId);
    }

    public static String getTenantId() {
        return TENANT_ID.get();
    }

    public static void setApiKey(String apiKey) {
        API_KEY.set(apiKey);
    }

    public static String getApiKey() {
        return API_KEY.get();
    }

    public static void setRequestId(String requestId) {
        REQUEST_ID.set(requestId);
    }

    public static String getRequestId() {
        return REQUEST_ID.get();
    }

    public static void setEmergency(boolean emergency) {
        EMERGENCY.set(emergency);
    }

    public static boolean isEmergency() {
        return EMERGENCY.get();
    }

    public static void clear() {
        TENANT_ID.remove();
        API_KEY.remove();
        REQUEST_ID.remove();
        EMERGENCY.remove();
    }
}

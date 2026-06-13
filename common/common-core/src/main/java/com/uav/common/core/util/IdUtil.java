package com.uav.common.core.util;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/**
 * ID生成工具
 */
public final class IdUtil {

    private IdUtil() {}

    private static final SecureRandom RANDOM = new SecureRandom();
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * 生成任务ID
     */
    public static String generateJobId() {
        return "job_" + LocalDateTime.now().format(DATE_FORMATTER) + "_" + randomAlphanumeric(8);
    }

    /**
     * 生成请求ID
     */
    public static String generateRequestId() {
        return "req_" + randomAlphanumeric(16);
    }

    /**
     * 生成API Key
     */
    public static String generateApiKey() {
        return "uk_" + randomAlphanumeric(32);
    }

    /**
     * 生成租户ID
     */
    public static String generateTenantId() {
        return "tenant_" + randomAlphanumeric(8);
    }

    /**
     * 生成UUID（无横线）
     */
    public static String fastUuid() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    private static String randomAlphanumeric(int length) {
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(chars.charAt(RANDOM.nextInt(chars.length())));
        }
        return sb.toString();
    }
}

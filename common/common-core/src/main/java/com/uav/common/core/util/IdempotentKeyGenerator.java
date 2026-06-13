package com.uav.common.core.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.util.DigestUtils;

import java.nio.charset.StandardCharsets;

/**
 * 幂等 Key 生成器
 * <p>
 * 基于请求参数 hash + tenantId + API 路径生成唯一幂等 Key。
 * Key 格式: {@code idempotent:{tenantId}:{apiPath}:{paramHash}}
 */
public final class IdempotentKeyGenerator {

    private static final String KEY_PREFIX = "idempotent:";
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private IdempotentKeyGenerator() {}

    /**
     * 生成幂等 Key
     *
     * @param tenantId 租户 ID
     * @param apiPath  API 路径（如 /api/v1/assimilation/tasks）
     * @param params   请求参数对象
     * @return 幂等 Key
     */
    public static String generate(String tenantId, String apiPath, Object params) {
        String paramHash = hashParams(params);
        return KEY_PREFIX + tenantId + ":" + apiPath + ":" + paramHash;
    }

    /**
     * 对请求参数进行 MD5 哈希
     *
     * @param params 请求参数对象
     * @return MD5 哈希值的十六进制字符串
     */
    private static String hashParams(Object params) {
        try {
            String json = OBJECT_MAPPER.writeValueAsString(params);
            return DigestUtils.md5DigestAsHex(json.getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            // 序列化失败时使用对象的 hashCode 作为降级方案
            return String.valueOf(params != null ? params.hashCode() : 0);
        }
    }
}

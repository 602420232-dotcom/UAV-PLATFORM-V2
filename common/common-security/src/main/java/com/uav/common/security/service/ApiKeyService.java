package com.uav.common.security.service;

/**
 * API Key 验证接口
 * <p>
 * 定义 API Key 与 Secret 的查询契约，具体存储实现由业务模块提供。
 */
public interface ApiKeyService {

    /**
     * 根据 API Key 查询对应的 Secret
     *
     * @param apiKey API Key
     * @return Secret，如果不存在则返回 null
     */
    String getSecretByApiKey(String apiKey);

    /**
     * 校验 API Key 是否有效
     *
     * @param apiKey API Key
     * @return true 表示有效
     */
    boolean isValidApiKey(String apiKey);
}

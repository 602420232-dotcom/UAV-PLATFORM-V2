package com.uav.platform.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.uav.platform.entity.ApiKey;
import com.uav.platform.mapper.ApiKeyMapper;
import com.uav.common.security.service.ApiKeyService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class ApiKeyServiceImpl extends ServiceImpl<ApiKeyMapper, ApiKey> implements ApiKeyService {

    private final ApiKeyMapper apiKeyMapper;
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();
    private static final Base64.Encoder BASE64_ENCODER = Base64.getUrlEncoder().withoutPadding();

    @Override
    public String getSecretByApiKey(String apiKey) {
        ApiKey key = apiKeyMapper.selectByKeyValue(apiKey);
        return key != null ? key.getSecret() : null;
    }

    @Override
    public boolean isValidApiKey(String apiKey) {
        ApiKey key = apiKeyMapper.selectByKeyValue(apiKey);
        if (key == null || key.getStatus() != 1) {
            return false;
        }
        if (key.getExpiresAt() != null && key.getExpiresAt().isBefore(LocalDateTime.now())) {
            return false;
        }
        return true;
    }

    public ApiKey getByKeyValue(String keyValue) {
        return apiKeyMapper.selectByKeyValue(keyValue);
    }

    @Transactional(rollbackFor = Exception.class)
    public ApiKey generateApiKey(Long tenantId, String name, Integer rateLimit, Integer expiresInDays) {
        String keyValue = generateRandomKey("ak_");
        String secret = generateRandomKey("sk_");

        ApiKey apiKey = new ApiKey();
        apiKey.setTenantId(tenantId);
        apiKey.setKeyValue(keyValue);
        apiKey.setSecret(secret);
        apiKey.setName(name);
        apiKey.setStatus(1);
        apiKey.setRateLimit(rateLimit != null ? rateLimit : 1000);
        apiKey.setCreatedAt(LocalDateTime.now());
        if (expiresInDays != null && expiresInDays > 0) {
            apiKey.setExpiresAt(LocalDateTime.now().plusDays(expiresInDays));
        }

        save(apiKey);
        log.info("Generated API key for tenant {}: {}", tenantId, keyValue);
        return apiKey;
    }

    @Transactional(rollbackFor = Exception.class)
    public void enableApiKey(Long id) {
        apiKeyMapper.updateStatusById(id, 1);
        log.info("Enabled API key: {}", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public void disableApiKey(Long id) {
        apiKeyMapper.updateStatusById(id, 0);
        log.info("Disabled API key: {}", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public void removeApiKey(Long id) {
        removeById(id);
        log.info("Removed API key: {}", id);
    }

    public List<ApiKey> listByTenant(Long tenantId) {
        return apiKeyMapper.selectByTenantId(tenantId);
    }

    private String generateRandomKey(String prefix) {
        byte[] bytes = new byte[32];
        SECURE_RANDOM.nextBytes(bytes);
        return prefix + BASE64_ENCODER.encodeToString(bytes);
    }
}

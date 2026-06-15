package com.uav.common.core.vault;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Vault 密钥提供者
 * 使用 HashiCorp Vault 客户端从 Vault 读取密钥
 * 支持本地文件回退（开发环境）
 * 密钥缓存（TTL 5 分钟）
 */
@Slf4j
@Component
public class VaultSecretProvider {

    @Value("${VAULT_ADDR:http://localhost:8200}")
    private String vaultAddr;

    @Value("${VAULT_TOKEN:}")
    private String vaultToken;

    @Value("${VAULT_NAMESPACE:}")
    private String vaultNamespace;

    @Value("${VAULT_KV_VERSION:2}")
    private int kvVersion;

    @Value("${VAULT_ENABLED:false}")
    private boolean vaultEnabled;

    @Value("${VAULT_SECRET_PATH_PREFIX:secret/uav-platform}")
    private String secretPathPrefix;

    @Value("${VAULT_CACHE_TTL_MINUTES:5}")
    private int cacheTtlMinutes;

    @Value("${VAULT_FALLBACK_FILE:classpath:vault-secrets.json}")
    private String fallbackFilePath;

    @Value("${spring.profiles.active:dev}")
    private String activeProfile;

    private static final Duration DEFAULT_CACHE_TTL = Duration.ofMinutes(5);
    private static final String VAULT_API_VERSION = "v1";

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final Map<String, CachedSecret> secretCache;
    private final ScheduledExecutorService cacheEvictionExecutor;

    private boolean vaultAvailable = false;

    public VaultSecretProvider() {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
        this.secretCache = new ConcurrentHashMap<>();
        this.cacheEvictionExecutor = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "vault-cache-eviction");
            t.setDaemon(true);
            return t;
        });
    }

    @PostConstruct
    public void init() {
        if (vaultEnabled) {
            checkVaultConnection();
        } else {
            log.warn("Vault integration is disabled. Using fallback file for secrets.");
        }

        // 启动缓存过期清理任务
        long evictionInterval = Math.max(cacheTtlMinutes, 1);
        cacheEvictionExecutor.scheduleAtFixedRate(
                this::evictExpiredSecrets,
                evictionInterval,
                evictionInterval,
                TimeUnit.MINUTES
        );

        log.info("VaultSecretProvider initialized. Vault enabled: {}, Cache TTL: {} minutes",
                vaultEnabled, cacheTtlMinutes);
    }

    /**
     * 检查 Vault 连接状态
     */
    private void checkVaultConnection() {
        try {
            HttpHeaders headers = createVaultHeaders();
            HttpEntity<Void> entity = new HttpEntity<>(headers);

            ResponseEntity<String> response = restTemplate.exchange(
                    vaultAddr + "/" + VAULT_API_VERSION + "/sys/health",
                    HttpMethod.GET,
                    entity,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                vaultAvailable = true;
                log.info("Successfully connected to Vault at {}", vaultAddr);
            } else {
                log.warn("Vault health check returned status: {}", response.getStatusCode());
            }
        } catch (Exception e) {
            vaultAvailable = false;
            log.warn("Failed to connect to Vault at {}: {}. Will use fallback file.", vaultAddr, e.getMessage());
        }
    }

    /**
     * 从 Vault 获取密钥
     *
     * @param secretPath 密钥路径（如 jwt, db, redis）
     * @param key        密钥名称（如 JWT_SECRET, DB_PASSWORD）
     * @return 密钥值
     */
    public String getSecret(String secretPath, String key) {
        String cacheKey = buildCacheKey(secretPath, key);

        // 1. 检查缓存
        CachedSecret cached = secretCache.get(cacheKey);
        if (cached != null && !cached.isExpired()) {
            log.debug("Cache hit for secret: {}/{}", secretPath, key);
            return cached.getValue();
        }

        // 2. 从 Vault 读取
        String value = null;
        if (vaultEnabled && vaultAvailable) {
            value = readFromVault(secretPath, key);
        }

        // 3. 回退到本地文件
        if (value == null) {
            value = readFromFallbackFile(secretPath, key);
        }

        // 4. 回退到环境变量
        if (value == null) {
            value = readFromEnvironment(key);
        }

        if (value != null) {
            // 写入缓存
            secretCache.put(cacheKey, new CachedSecret(value, Duration.ofMinutes(cacheTtlMinutes)));
            log.debug("Secret cached: {}/{}", secretPath, key);
        } else {
            log.error("Failed to retrieve secret: {}/{} from all sources", secretPath, key);
        }

        return value;
    }

    /**
     * 从 Vault 读取密钥
     */
    private String readFromVault(String secretPath, String key) {
        try {
            String fullPath = buildVaultPath(secretPath);
            HttpHeaders headers = createVaultHeaders();
            HttpEntity<Void> entity = new HttpEntity<>(headers);

            ResponseEntity<String> response = restTemplate.exchange(
                    fullPath,
                    HttpMethod.GET,
                    entity,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                JsonNode root = objectMapper.readTree(response.getBody());
                JsonNode dataNode;

                if (kvVersion == 2) {
                    // KV v2: data -> data -> key
                    dataNode = root.path("data").path("data");
                } else {
                    // KV v1: data -> key
                    dataNode = root.path("data");
                }

                JsonNode valueNode = dataNode.path(key);
                if (!valueNode.isMissingNode()) {
                    String value = valueNode.asText();
                    log.debug("Secret retrieved from Vault: {}/{}", secretPath, key);
                    return value;
                } else {
                    log.warn("Key '{}' not found in Vault secret: {}", key, secretPath);
                }
            }
        } catch (RestClientResponseException e) {
            log.error("Vault API error for secret '{}': {} - {}", secretPath, e.getStatusCode(), e.getResponseBodyAsString());
        } catch (Exception e) {
            log.error("Error reading from Vault for secret '{}': {}", secretPath, e.getMessage());
        }

        return null;
    }

    /**
     * 从本地回退文件读取密钥
     */
    private String readFromFallbackFile(String secretPath, String key) {
        try {
            Resource resource = loadFallbackResource();
            if (!resource.exists()) {
                log.debug("Fallback file not found: {}", fallbackFilePath);
                return null;
            }

            JsonNode root = objectMapper.readTree(resource.getInputStream());
            JsonNode envNode = root.path(activeProfile);
            if (envNode.isMissingNode()) {
                envNode = root.path("dev"); // 默认使用 dev 环境
            }

            JsonNode secretNode = envNode.path(secretPath);
            if (!secretNode.isMissingNode()) {
                JsonNode valueNode = secretNode.path(key);
                if (!valueNode.isMissingNode()) {
                    String value = valueNode.asText();
                    log.debug("Secret retrieved from fallback file: {}/{}", secretPath, key);
                    return value;
                }
            }
        } catch (IOException e) {
            log.error("Error reading fallback file '{}': {}", fallbackFilePath, e.getMessage());
        }

        return null;
    }

    /**
     * 从环境变量读取密钥
     */
    private String readFromEnvironment(String key) {
        String value = System.getenv(key);
        if (value != null) {
            log.debug("Secret retrieved from environment variable: {}", key);
        }
        return value;
    }

    /**
     * 构建 Vault 完整路径
     */
    private String buildVaultPath(String secretPath) {
        String path = secretPathPrefix + "/" + activeProfile + "/" + secretPath;
        if (kvVersion == 2) {
            return vaultAddr + "/" + VAULT_API_VERSION + "/" + path;
        }
        return vaultAddr + "/" + VAULT_API_VERSION + "/" + path;
    }

    /**
     * 构建缓存键
     */
    private String buildCacheKey(String secretPath, String key) {
        return activeProfile + ":" + secretPath + ":" + key;
    }

    /**
     * 创建 Vault HTTP 请求头
     */
    private HttpHeaders createVaultHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Vault-Token", vaultToken);
        if (vaultNamespace != null && !vaultNamespace.isEmpty()) {
            headers.set("X-Vault-Namespace", vaultNamespace);
        }
        return headers;
    }

    /**
     * 加载回退资源文件
     */
    private Resource loadFallbackResource() {
        if (fallbackFilePath.startsWith("classpath:")) {
            return new ClassPathResource(fallbackFilePath.substring("classpath:".length()));
        } else if (fallbackFilePath.startsWith("file:")) {
            return new FileSystemResource(fallbackFilePath.substring("file:".length()));
        } else {
            Path path = Paths.get(fallbackFilePath);
            if (Files.exists(path)) {
                return new FileSystemResource(path.toString());
            }
            return new ClassPathResource(fallbackFilePath);
        }
    }

    /**
     * 清理过期缓存
     */
    private void evictExpiredSecrets() {
        int beforeSize = secretCache.size();
        secretCache.entrySet().removeIf(entry -> entry.getValue().isExpired());
        int afterSize = secretCache.size();
        int removed = beforeSize - afterSize;
        if (removed > 0) {
            log.debug("Evicted {} expired secrets from cache. Current cache size: {}", removed, afterSize);
        }
    }

    /**
     * 强制刷新指定密钥（清除缓存并重新读取）
     *
     * @param secretPath 密钥路径
     * @param key        密钥名称
     * @return 刷新后的密钥值
     */
    public String refreshSecret(String secretPath, String key) {
        String cacheKey = buildCacheKey(secretPath, key);
        secretCache.remove(cacheKey);
        log.info("Cache invalidated for secret: {}/{}", secretPath, key);
        return getSecret(secretPath, key);
    }

    /**
     * 批量获取密钥
     *
     * @param secretPath 密钥路径
     * @param keys       密钥名称列表
     * @return 密钥映射
     */
    public Map<String, String> getSecrets(String secretPath, String... keys) {
        Map<String, String> result = new ConcurrentHashMap<>();
        for (String key : keys) {
            String value = getSecret(secretPath, key);
            if (value != null) {
                result.put(key, value);
            }
        }
        return result;
    }

    /**
     * 检查 Vault 是否可用
     */
    public boolean isVaultAvailable() {
        return vaultEnabled && vaultAvailable;
    }

    /**
     * 获取缓存统计信息
     */
    public Map<String, Object> getCacheStats() {
        Map<String, Object> stats = new ConcurrentHashMap<>();
        stats.put("cacheSize", secretCache.size());
        stats.put("vaultEnabled", vaultEnabled);
        stats.put("vaultAvailable", vaultAvailable);
        stats.put("cacheTtlMinutes", cacheTtlMinutes);
        return stats;
    }

    /**
     * 关闭资源
     */
    public void shutdown() {
        cacheEvictionExecutor.shutdown();
        try {
            if (!cacheEvictionExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                cacheEvictionExecutor.shutdownNow();
            }
        } catch (InterruptedException e) {
            cacheEvictionExecutor.shutdownNow();
            Thread.currentThread().interrupt();
        }
        log.info("VaultSecretProvider shutdown complete");
    }

    /**
     * 缓存条目
     */
    private static class CachedSecret {
        private final String value;
        private final Instant expiryTime;

        CachedSecret(String value, Duration ttl) {
            this.value = value;
            this.expiryTime = Instant.now().plus(ttl);
        }

        String getValue() {
            return value;
        }

        boolean isExpired() {
            return Instant.now().isAfter(expiryTime);
        }
    }
}

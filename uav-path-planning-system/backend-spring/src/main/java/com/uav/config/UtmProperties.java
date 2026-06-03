package com.uav.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * UTM (Unmanned Traffic Management) 配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "utm")
public class UtmProperties {

    /**
     * 是否启用 UTM 集成
     */
    private boolean enabled = false;

    /**
     * UTM 提供商名称
     */
    private String provider = "simulation";

    /**
     * API 配置
     */
    private Api api = new Api();

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public String getProvider() {
        return provider;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public Api getApi() {
        return api;
    }

    public void setApi(Api api) {
        this.api = api;
    }

    public static class Api {
        /**
         * UTM API 基础 URL
         */
        private String baseUrl = "https://api.utm-platform.com/v1";

        /**
         * UTM API 密钥
         */
        private String key;

        /**
         * API 请求超时时间（毫秒）
         */
        private int timeout = 5000;

        public String getBaseUrl() {
            return baseUrl;
        }

        public void setBaseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
        }

        public String getKey() {
            return key;
        }

        public void setKey(String key) {
            this.key = key;
        }

        public int getTimeout() {
            return timeout;
        }

        public void setTimeout(int timeout) {
            this.timeout = timeout;
        }
    }
}

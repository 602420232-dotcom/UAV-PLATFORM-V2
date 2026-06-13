package com.uav.sdk;

import com.uav.sdk.api.AssimilationApi;
import com.uav.sdk.api.PlanningApi;
import com.uav.sdk.api.RiskApi;
import com.uav.sdk.api.UtmApi;
import com.uav.sdk.api.WeatherApi;
import com.uav.sdk.config.ClientConfig;
import com.uav.sdk.http.HttpClientWrapper;

import java.util.Objects;

/**
 * UAV Platform SDK 入口
 * <p>
 * 使用 Builder 模式构建客户端实例，通过各 API 子模块访问平台功能。
 * <p>
 * 使用示例:
 * <pre>
 * try (UavPlatformClient client = UavPlatformClient.builder()
 *         .baseUrl("http://localhost:8080")
 *         .apiKey("your-api-key")
 *         .apiSecret("your-api-secret")
 *         .build()) {
 *
 *     WeatherGrid weather = client.weather().queryPoint(104.07, 30.67, null);
 *     String taskId = client.assimilation().submitTask("5DVAR", params);
 *     TaskResult result = client.assimilation().getTaskResult(taskId);
 * }
 * </pre>
 */
public class UavPlatformClient implements AutoCloseable {

    private final ClientConfig config;
    private final HttpClientWrapper httpClient;

    private UavPlatformClient(ClientConfig config) {
        Objects.requireNonNull(config, "ClientConfig 不能为 null");
        Objects.requireNonNull(config.getBaseUrl(), "baseUrl 不能为 null");
        this.config = config;
        this.httpClient = new HttpClientWrapper(config);
    }

    /**
     * 创建 Builder 实例
     */
    public static Builder builder() {
        return new Builder();
    }

    /**
     * 获取气象数据 API
     */
    public WeatherApi weather() {
        return new WeatherApi(httpClient, config);
    }

    /**
     * 获取数据同化 API
     */
    public AssimilationApi assimilation() {
        return new AssimilationApi(httpClient, config);
    }

    /**
     * 获取路径规划 API
     */
    public PlanningApi planning() {
        return new PlanningApi(httpClient, config);
    }

    /**
     * 获取风险评估 API
     */
    public RiskApi risk() {
        return new RiskApi(httpClient, config);
    }

    /**
     * 获取 UTM 管理 API
     */
    public UtmApi utm() {
        return new UtmApi(httpClient, config);
    }

    /**
     * 获取客户端配置
     */
    public ClientConfig getConfig() {
        return config;
    }

    @Override
    public void close() {
        httpClient.close();
    }

    /**
     * Builder 模式构建器
     */
    public static class Builder {

        private final ClientConfig config = new ClientConfig();

        public Builder baseUrl(String baseUrl) {
            config.setBaseUrl(baseUrl);
            return this;
        }

        public Builder apiKey(String apiKey) {
            config.setApiKey(apiKey);
            return this;
        }

        public Builder apiSecret(String apiSecret) {
            config.setApiSecret(apiSecret);
            return this;
        }

        public Builder connectTimeoutSeconds(int seconds) {
            config.setConnectTimeoutSeconds(seconds);
            return this;
        }

        public Builder readTimeoutSeconds(int seconds) {
            config.setReadTimeoutSeconds(seconds);
            return this;
        }

        public UavPlatformClient build() {
            return new UavPlatformClient(config);
        }
    }
}

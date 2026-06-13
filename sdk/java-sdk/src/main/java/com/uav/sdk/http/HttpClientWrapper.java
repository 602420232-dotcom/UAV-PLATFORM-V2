package com.uav.sdk.http;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.uav.sdk.auth.SignatureUtil;
import com.uav.sdk.config.ClientConfig;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;

/**
 * HTTP 客户端封装
 * <p>
 * 基于 JDK 21 HttpClient 实现，自动处理 HMAC 签名和 JSON 序列化。
 */
public class HttpClientWrapper implements AutoCloseable {

    private final ClientConfig config;
    private final java.net.http.HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public HttpClientWrapper(ClientConfig config) {
        this.config = config;
        this.httpClient = java.net.http.HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(config.getConnectTimeoutSeconds()))
                .build();
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        this.objectMapper.disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
    }

    /**
     * 发送 GET 请求
     *
     * @param path    API 路径
     * @param headers 额外请求头
     * @return 响应体 JSON 字符串
     */
    public String get(String path, Map<String, String> headers) throws IOException, InterruptedException {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(config.getBaseUrl() + path))
                .timeout(Duration.ofSeconds(config.getReadTimeoutSeconds()))
                .GET();

        applyAuthHeaders(builder, "GET", path, null);
        if (headers != null) {
            headers.forEach(builder::header);
        }

        HttpResponse<String> response = httpClient.send(builder.build(),
                HttpResponse.BodyHandlers.ofString());
        return handleResponse(response);
    }

    /**
     * 发送 GET 请求（无额外请求头）
     */
    public String get(String path) throws IOException, InterruptedException {
        return get(path, null);
    }

    /**
     * 发送 POST 请求
     *
     * @param path    API 路径
     * @param body    请求体对象
     * @param headers 额外请求头
     * @return 响应体 JSON 字符串
     */
    public String post(String path, Object body, Map<String, String> headers)
            throws IOException, InterruptedException {
        String jsonBody = body != null ? objectMapper.writeValueAsString(body) : "";

        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(config.getBaseUrl() + path))
                .timeout(Duration.ofSeconds(config.getReadTimeoutSeconds()))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonBody));

        applyAuthHeaders(builder, "POST", path, jsonBody);
        if (headers != null) {
            headers.forEach(builder::header);
        }

        HttpResponse<String> response = httpClient.send(builder.build(),
                HttpResponse.BodyHandlers.ofString());
        return handleResponse(response);
    }

    /**
     * 发送 POST 请求（无额外请求头）
     */
    public String post(String path, Object body) throws IOException, InterruptedException {
        return post(path, body, null);
    }

    /**
     * 发送 GET 请求并反序列化响应
     *
     * @param path API 路径
     * @param type 返回类型
     * @return 反序列化后的对象
     */
    public <T> SdkResponse<T> getAndDeserialize(String path, TypeReference<SdkResponse<T>> type)
            throws IOException, InterruptedException {
        String json = get(path);
        return objectMapper.readValue(json, type);
    }

    /**
     * 发送 POST 请求并反序列化响应
     *
     * @param path API 路径
     * @param body 请求体对象
     * @param type 返回类型
     * @return 反序列化后的对象
     */
    public <T> SdkResponse<T> postAndDeserialize(String path, Object body,
                                                     TypeReference<SdkResponse<T>> type)
            throws IOException, InterruptedException {
        String json = post(path, body);
        return objectMapper.readValue(json, type);
    }

    /**
     * 获取 ObjectMapper 实例（供外部使用）
     */
    public ObjectMapper getObjectMapper() {
        return objectMapper;
    }

    /**
     * 应用 HMAC 签名认证头
     */
    private void applyAuthHeaders(HttpRequest.Builder builder, String method,
                                   String path, String body) {
        if (config.getApiKey() == null || config.getApiSecret() == null) {
            return;
        }

        String timestamp = String.valueOf(Instant.now().getEpochSecond());
        String signString = SignatureUtil.buildSignString(
                method, path, timestamp, config.getApiKey(), body);
        String signature = SignatureUtil.sign(signString, config.getApiSecret());

        builder.header("X-API-Key", config.getApiKey());
        builder.header("X-Timestamp", timestamp);
        builder.header("X-Signature", signature);
    }

    /**
     * 处理 HTTP 响应
     */
    private String handleResponse(HttpResponse<String> response) throws IOException {
        if (response.statusCode() >= 200 && response.statusCode() < 300) {
            return response.body();
        }
        throw new IOException("HTTP 请求失败, status=" + response.statusCode()
                + ", body=" + response.body());
    }

    @Override
    public void close() {
        // JDK HttpClient 无需显式关闭
    }

    /**
     * SDK 统一响应结构
     *
     * @param <T> 数据类型
     */
    public static class SdkResponse<T> {
        private int code;
        private String message;
        private T data;
        private String requestId;
        private long timestamp;

        public int getCode() { return code; }
        public void setCode(int code) { this.code = code; }
        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }
        public T getData() { return data; }
        public void setData(T data) { this.data = data; }
        public String getRequestId() { return requestId; }
        public void setRequestId(String requestId) { this.requestId = requestId; }
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }

        public boolean isSuccess() {
            return this.code == 200;
        }
    }
}

package com.uav.sdk.api;

import com.fasterxml.jackson.core.type.TypeReference;
import com.uav.sdk.config.ClientConfig;
import com.uav.sdk.http.HttpClientWrapper;
import com.uav.sdk.http.HttpClientWrapper.SdkResponse;
import com.uav.sdk.model.WeatherGrid;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

/**
 * 气象数据 API
 * <p>
 * 提供气象数据查询功能，包括点查询、网格查询和预报查询。
 */
public class WeatherApi {

    private static final String BASE_PATH = "/api/v1/weather";

    private final HttpClientWrapper httpClient;
    private final ClientConfig config;

    public WeatherApi(HttpClientWrapper httpClient, ClientConfig config) {
        this.httpClient = httpClient;
        this.config = config;
    }

    /**
     * 查询指定点的气象数据
     *
     * @param longitude    经度
     * @param latitude     纬度
     * @param forecastTime 预报时间（ISO 格式，可为 null）
     * @return 气象网格数据
     */
    public WeatherGrid queryPoint(double longitude, double latitude, String forecastTime)
            throws IOException, InterruptedException {
        String path = BASE_PATH + "/point?longitude=" + longitude
                + "&latitude=" + latitude;
        if (forecastTime != null) {
            path += "&forecastTime=" + URLEncoder.encode(forecastTime, StandardCharsets.UTF_8);
        }
        SdkResponse<WeatherGrid> response = httpClient.getAndDeserialize(
                path, new TypeReference<SdkResponse<WeatherGrid>>() {});
        return response.getData();
    }

    /**
     * 查询气象网格数据
     *
     * @param minLon 最小经度
     * @param minLat 最小纬度
     * @param maxLon 最大经度
     * @param maxLat 最大纬度
     * @return 气象网格数据
     */
    public WeatherGrid queryGrid(double minLon, double minLat, double maxLon, double maxLat)
            throws IOException, InterruptedException {
        String path = BASE_PATH + "/grid?minLon=" + minLon
                + "&minLat=" + minLat
                + "&maxLon=" + maxLon
                + "&maxLat=" + maxLat;
        SdkResponse<WeatherGrid> response = httpClient.getAndDeserialize(
                path, new TypeReference<SdkResponse<WeatherGrid>>() {});
        return response.getData();
    }
}

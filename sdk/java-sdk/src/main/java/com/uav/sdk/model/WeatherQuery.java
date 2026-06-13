package com.uav.sdk.model;

import java.util.List;
import java.util.Map;

/**
 * 气象数据查询参数
 */
public class WeatherQuery {

    private Double longitude;
    private Double latitude;
    private String forecastTime;
    private List<String> variables;

    public WeatherQuery() {}

    public WeatherQuery(Double longitude, Double latitude, String forecastTime) {
        this.longitude = longitude;
        this.latitude = latitude;
        this.forecastTime = forecastTime;
    }

    public Double getLongitude() { return longitude; }
    public void setLongitude(Double longitude) { this.longitude = longitude; }
    public Double getLatitude() { return latitude; }
    public void setLatitude(Double latitude) { this.latitude = latitude; }
    public String getForecastTime() { return forecastTime; }
    public void setForecastTime(String forecastTime) { this.forecastTime = forecastTime; }
    public List<String> getVariables() { return variables; }
    public void setVariables(List<String> variables) { this.variables = variables; }
}

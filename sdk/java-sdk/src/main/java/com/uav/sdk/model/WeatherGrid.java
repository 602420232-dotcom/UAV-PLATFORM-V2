package com.uav.sdk.model;

import java.util.Map;

/**
 * 气象网格数据
 */
public class WeatherGrid {

    private Map<String, Object> wind;
    private Map<String, Object> temperature;
    private Map<String, Object> humidity;
    private Map<String, Object> pressure;
    private Map<String, Object> precipitation;
    private Map<String, Object> visibility;
    private String forecastTime;
    private String gridResolution;

    public Map<String, Object> getWind() { return wind; }
    public void setWind(Map<String, Object> wind) { this.wind = wind; }
    public Map<String, Object> getTemperature() { return temperature; }
    public void setTemperature(Map<String, Object> temperature) { this.temperature = temperature; }
    public Map<String, Object> getHumidity() { return humidity; }
    public void setHumidity(Map<String, Object> humidity) { this.humidity = humidity; }
    public Map<String, Object> getPressure() { return pressure; }
    public void setPressure(Map<String, Object> pressure) { this.pressure = pressure; }
    public Map<String, Object> getPrecipitation() { return precipitation; }
    public void setPrecipitation(Map<String, Object> precipitation) { this.precipitation = precipitation; }
    public Map<String, Object> getVisibility() { return visibility; }
    public void setVisibility(Map<String, Object> visibility) { this.visibility = visibility; }
    public String getForecastTime() { return forecastTime; }
    public void setForecastTime(String forecastTime) { this.forecastTime = forecastTime; }
    public String getGridResolution() { return gridResolution; }
    public void setGridResolution(String gridResolution) { this.gridResolution = gridResolution; }
}

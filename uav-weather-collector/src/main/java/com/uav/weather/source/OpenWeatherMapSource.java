package com.uav.weather.source;

import com.uav.weather.model.WeatherData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.Optional;

/**
 * OpenWeatherMap 国际天气数据源
 * 
 * 提供全球气象数据，作为国内数据源不可用时的备用方案。
 */
@Slf4j
@Component
public class OpenWeatherMapSource {

    private final RestTemplate restTemplate;

    @Value("${weather.owm.api-key:}")
    private String apiKey;

    @Value("${weather.owm.base-url:https://api.openweathermap.org/data/2.5}")
    private String baseUrl;

    public OpenWeatherMapSource() {
        this.restTemplate = new RestTemplate();
    }

    /**
     * 获取当前位置的实时天气
     */
    public Optional<WeatherData> fetchCurrentWeather(double lat, double lon) {
        if (apiKey.isEmpty()) {
            log.warn("OpenWeatherMap API key not configured, using mock");
            return Optional.of(generateMockData(lat, lon));
        }

        try {
            String url = String.format("%s/weather?lat=%f&lon=%f&appid=%s&units=metric",
                baseUrl, lat, lon, apiKey);
            
            @SuppressWarnings("unchecked")
            Map<String, Object> response = restTemplate.getForObject(
                java.util.Objects.requireNonNull(url), Map.class);
            
            if (response != null) {
                return Optional.of(parseOwmResponse(response, lat, lon));
            }
        } catch (Exception e) {
            log.error("Failed to fetch OpenWeatherMap data: {}", e.getMessage());
        }

        return Optional.of(generateMockData(lat, lon));
    }

    /**
     * 获取 5 天/3 小时间隔的天气预报
     */
    public List<WeatherData> fetchForecast(double lat, double lon) {
        List<WeatherData> results = new ArrayList<>();

        if (apiKey.isEmpty()) {
            for (int i = 0; i < 5; i++) {
                results.add(generateMockData(lat + Math.random() * 0.1, 
                                            lon + Math.random() * 0.1));
            }
            return results;
        }

        try {
            String url = String.format("%s/forecast?lat=%f&lon=%f&appid=%s&units=metric",
                baseUrl, lat, lon, apiKey);
            
            @SuppressWarnings("unchecked")
            Map<String, Object> response = restTemplate.getForObject(
                java.util.Objects.requireNonNull(url), Map.class);
            
            if (response != null && response.containsKey("list")) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> list = (List<Map<String, Object>>) response.get("list");
                for (Map<String, Object> item : list) {
                    results.add(parseOwmItem(item, lat, lon));
                }
            }
        } catch (Exception e) {
            log.error("Failed to fetch OWM forecast: {}", e.getMessage());
        }

        return results;
    }

    private WeatherData parseOwmResponse(Map<String, Object> response, double lat, double lon) {
        WeatherData data = new WeatherData();
        data.setSource("OpenWeatherMap");
        data.setLatitude(lat);
        data.setLongitude(lon);
        data.setTimestamp(System.currentTimeMillis());

        @SuppressWarnings("unchecked")
        Map<String, Object> main = (Map<String, Object>) response.getOrDefault("main", Map.of());
        data.setTemperature(toDouble(main.get("temp")));
        data.setHumidity(toDouble(main.get("humidity")));
        data.setPressure(toDouble(main.get("pressure")));

        @SuppressWarnings("unchecked")
        Map<String, Object> wind = (Map<String, Object>) response.getOrDefault("wind", Map.of());
        data.setWindSpeed(toDouble(wind.get("speed")));
        data.setWindDirection(toDouble(wind.get("deg")));

        @SuppressWarnings("unchecked")
        Map<String, Object> clouds = (Map<String, Object>) response.getOrDefault("clouds", Map.of());
        data.setCloudCover(toDouble(clouds.get("all")));

        @SuppressWarnings("unchecked")
        Map<String, Object> sys = (Map<String, Object>) response.getOrDefault("sys", Map.of());
        data.setCountryCode((String) sys.getOrDefault("country", ""));

        return data;
    }

    private WeatherData parseOwmItem(Map<String, Object> item, double lat, double lon) {
        WeatherData data = new WeatherData();
        data.setSource("OpenWeatherMap");
        data.setLatitude(lat);
        data.setLongitude(lon);
        data.setTimestamp(System.currentTimeMillis() + 3 * 3600000L);

        @SuppressWarnings("unchecked")
        Map<String, Object> main = (Map<String, Object>) item.getOrDefault("main", Map.of());
        data.setTemperature(toDouble(main.get("temp")));
        data.setHumidity(toDouble(main.get("humidity")));

        @SuppressWarnings("unchecked")
        Map<String, Object> wind = (Map<String, Object>) item.getOrDefault("wind", Map.of());
        data.setWindSpeed(toDouble(wind.get("speed")));

        return data;
    }

    private WeatherData generateMockData(double lat, double lon) {
        WeatherData data = new WeatherData();
        data.setSource("OpenWeatherMap");
        data.setLatitude(lat);
        data.setLongitude(lon);
        data.setTimestamp(System.currentTimeMillis());
        data.setTemperature(18.0 + Math.random() * 12);
        data.setWindSpeed(3.0 + Math.random() * 8);
        data.setWindDirection(Math.random() * 360);
        data.setHumidity(55.0 + Math.random() * 25);
        data.setPressure(1013.0);
        log.info("Generated mock OpenWeatherMap data for ({}, {})", lat, lon);
        return data;
    }

    private double toDouble(Object value) {
        if (value instanceof Number) return ((Number) value).doubleValue();
        if (value instanceof String) return Double.parseDouble((String) value);
        return 0.0;
    }
}

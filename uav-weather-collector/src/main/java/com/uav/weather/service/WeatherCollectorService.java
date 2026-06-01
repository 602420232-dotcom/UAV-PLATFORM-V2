package com.uav.weather.service;
import com.uav.weather.model.WeatherData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.ArrayDeque;
import java.util.Deque;

@Service
public class WeatherCollectorService {

    private static final Logger log = LoggerFactory.getLogger(WeatherCollectorService.class);

    private final Map<String, Deque<WeatherData>> droneWeatherBuffer = new ConcurrentHashMap<>();
    private final Map<String, List<Map<String, Object>>> alertHistory = new ConcurrentHashMap<>();
    private final List<Map<String, Object>> dataSources = new CopyOnWriteArrayList<>();

    private static final double WIND_SPEED_THRESHOLD = 12.0;
    private static final double WIND_GUST_THRESHOLD = 18.0;
    private static final double VISIBILITY_MIN = 2.0;

    @PostConstruct
    public void init() {
        dataSources.add(Map.of("id", "wrf", "name", "WRF模型", "type", "model", "status", "online"));
        dataSources.add(Map.of("id", "uav_sensor", "name", "无人机传感器", "type", "sensor", "status", "online"));
        dataSources.add(Map.of("id", "ground_station", "name", "地面气象站", "type", "station", "status", "online"));
        dataSources.add(Map.of("id", "satellite", "name", "卫星遥感", "type", "satellite", "status", "online"));
        dataSources.add(Map.of("id", "buoy", "name", "浮标站", "type", "buoy", "status", "online"));
        log.info("气象数据源初始化完成: {} 个数据源", dataSources.size());
    }

    public Map<String, Object> collectFromUAVSensor(Map<String, Object> data) {
        return collect("uav_sensor", data, 0.9);
    }

    public Map<String, Object> collectFromWRFModel(Map<String, Object> data) {
        return collect("wrf", data, 0.8);
    }

    public Map<String, Object> collectFromGroundStation(Map<String, Object> data) {
        return collect("ground_station", data, 0.85);
    }

    private Map<String, Object> collect(String source, Map<String, Object> data, double quality) {
        String droneId = (String) data.getOrDefault("drone_id", "unknown");
        WeatherData record = new WeatherData();
        record.setSource(source);
        record.setDroneId(droneId);
        record.setTimestamp(Instant.now().toEpochMilli());
        record.setLatitude(getDouble(data, "latitude"));
        record.setLongitude(getDouble(data, "longitude"));
        record.setAltitude(getDouble(data, "altitude"));
        record.setTemperature(getDouble(data, "temperature"));
        record.setHumidity(getDouble(data, "humidity"));
        record.setWindSpeed(getDouble(data, "wind_speed"));
        record.setWindDirection(getDouble(data, "wind_direction"));
        record.setWindGust(getDouble(data, "wind_gust"));
        record.setPressure(getDouble(data, "pressure"));
        record.setVisibility(getDouble(data, "visibility"));
        record.setTurbulence(getDouble(data, "turbulence"));
        record.setPrecipitation(getDouble(data, "precipitation"));
        record.setDataQuality(quality);

        droneWeatherBuffer.computeIfAbsent(droneId, k -> new ArrayDeque<>()).addLast(record);
        log.info("气象数据已收集: source={}, drone={}, wind={}m/s", source, droneId, record.getWindSpeed());

        Map<String, Object> alert = evaluateAlertInternal(droneId, record);
        if (alert != null) {
            alertHistory.computeIfAbsent(droneId, k -> new CopyOnWriteArrayList<>()).add(alert);
        }

        return Map.of("success", true, "drone_id", droneId, "data_quality", quality);
    }

    public Map<String, Object> getCurrentWeather(String droneId) {
        Deque<WeatherData> buffer = droneWeatherBuffer.get(droneId);
        if (buffer == null || buffer.isEmpty()) {
            return Map.of("success", false, "error", "暂无数据");
        }
        WeatherData latest = buffer.getLast();
        return Map.of("success", true, "data", latest.toMap());
    }

    public List<Map<String, Object>> getWeatherHistory(String droneId, int minutes) {
        Deque<WeatherData> buffer = droneWeatherBuffer.get(droneId);
        if (buffer == null || buffer.isEmpty()) return List.of();
        long cutoff = Instant.now().toEpochMilli() - minutes * 60000L;
        return buffer.stream()
                .filter(w -> w.getTimestamp() > cutoff)
                .map(WeatherData::toMap)
                .collect(Collectors.toList());
    }

    public Map<String, Object> getFusedWeather(String droneId) {
        Deque<WeatherData> buffer = droneWeatherBuffer.get(droneId);
        if (buffer == null || buffer.isEmpty()) {
            return Map.of("success", false, "error", "暂无数据");
        }
        WeatherData sensor = null, wrf = null;
        for (WeatherData w : buffer) {
            if ("uav_sensor".equals(w.getSource()) && sensor == null) sensor = w;
            if ("wrf".equals(w.getSource()) && wrf == null) wrf = w;
            if (sensor != null && wrf != null) break;
        }
        if (sensor == null) return Map.of("success", false, "error", "无传感器数据");
        double fusedWind = sensor.getWindSpeed() * 0.7 + (wrf != null ? wrf.getWindSpeed() : sensor.getWindSpeed()) * 0.3;
        return Map.of("success", true, "drone_id", droneId,
                "wind_speed", fusedWind,
                "temperature", sensor.getTemperature(),
                "humidity", sensor.getHumidity(),
                "source_fusion", wrf != null ? "sensor+wrf" : "sensor_only");
    }

    public Map<String, Object> evaluateAlert(Map<String, Object> weatherData) {
        List<String> warnings = new ArrayList<>();
        double wind = getDouble(weatherData, "wind_speed");
        double gust = getDouble(weatherData, "wind_gust");
        double vis = getDouble(weatherData, "visibility");
        if (wind > WIND_SPEED_THRESHOLD) warnings.add("风速告警: " + wind + "m/s");
        if (gust > WIND_GUST_THRESHOLD) warnings.add("阵风告警: " + gust + "m/s");
        if (vis < VISIBILITY_MIN) warnings.add("能见度过低: " + vis + "km");
        return Map.of("has_alert", !warnings.isEmpty(), "warnings", warnings,
                "level", warnings.size() >= 2 ? "HIGH" : "MEDIUM");
    }

    private Map<String, Object> evaluateAlertInternal(String droneId, WeatherData w) {
        List<String> warnings = new ArrayList<>();
        if (w.getWindSpeed() > WIND_SPEED_THRESHOLD) warnings.add("风速告警: " + w.getWindSpeed() + "m/s");
        if (w.getWindGust() > WIND_GUST_THRESHOLD) warnings.add("阵风告警: " + w.getWindGust() + "m/s");
        if (w.getVisibility() < VISIBILITY_MIN) warnings.add("能见度过低: " + w.getVisibility() + "km");
        if (warnings.isEmpty()) return null;
        return Map.of("drone_id", droneId, "timestamp", Instant.now().toEpochMilli(),
                "warnings", warnings, "level", warnings.size() >= 2 ? "HIGH" : "MEDIUM");
    }

    public List<Map<String, Object>> getDroneAlerts(String droneId) {
        return alertHistory.getOrDefault(droneId, List.of());
    }

    public List<Map<String, Object>> listDataSources() {
        return dataSources;
    }

    private double getDouble(Map<String, Object> map, String key) {
        Object val = map.get(key);
        if (val instanceof Number) return ((Number) val).doubleValue();
        return 0.0;
    }
}

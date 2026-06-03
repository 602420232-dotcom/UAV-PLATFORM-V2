package com.uav.weather.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.weather.config.WeatherProperties;
import com.uav.weather.model.WeatherData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
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
import java.util.HashMap;

@Service
public class WeatherCollectorService {

    private static final Logger log = LoggerFactory.getLogger(WeatherCollectorService.class);

    private final Map<String, Deque<WeatherData>> droneWeatherBuffer = new ConcurrentHashMap<>();
    private final Map<String, List<Map<String, Object>>> alertHistory = new ConcurrentHashMap<>();
    private final List<Map<String, Object>> dataSources = new CopyOnWriteArrayList<>();

    private static final double WIND_SPEED_THRESHOLD = 12.0;
    private static final double WIND_GUST_THRESHOLD = 18.0;
    private static final double VISIBILITY_MIN = 2.0;
    private static final double TURBULENCE_THRESHOLD = 0.5;

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    @SuppressWarnings("unused")
    private final WeatherProperties weatherProperties;

    public WeatherCollectorService(RestTemplate restTemplate, WeatherProperties weatherProperties) {
        this.restTemplate = restTemplate;
        this.objectMapper = new ObjectMapper();
        this.weatherProperties = weatherProperties;
    }

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
        WeatherData sensor = null, wrf = null, ground = null;
        for (WeatherData w : buffer) {
            if ("uav_sensor".equals(w.getSource()) && sensor == null) sensor = w;
            if ("wrf".equals(w.getSource()) && wrf == null) wrf = w;
            if ("ground_station".equals(w.getSource()) && ground == null) ground = w;
            if (sensor != null && wrf != null && ground != null) break;
        }
        if (sensor == null) return Map.of("success", false, "error", "无传感器数据");
        
        double fusedWind = calculateFusedValue(
                sensor.getWindSpeed(), sensor.getDataQuality(),
                wrf != null ? wrf.getWindSpeed() : 0, wrf != null ? wrf.getDataQuality() : 0,
                ground != null ? ground.getWindSpeed() : 0, ground != null ? ground.getDataQuality() : 0);
        double fusedTemp = calculateFusedValue(
                sensor.getTemperature(), sensor.getDataQuality(),
                wrf != null ? wrf.getTemperature() : 0, wrf != null ? wrf.getDataQuality() : 0,
                ground != null ? ground.getTemperature() : 0, ground != null ? ground.getDataQuality() : 0);

        List<String> sources = new ArrayList<>();
        if (sensor != null) sources.add("sensor");
        if (wrf != null) sources.add("wrf");
        if (ground != null) sources.add("ground");

        return Map.of("success", true, "drone_id", droneId,
                "wind_speed", fusedWind,
                "temperature", fusedTemp,
                "humidity", sensor.getHumidity(),
                "visibility", sensor.getVisibility(),
                "source_fusion", String.join("+", sources));
    }

    private double calculateFusedValue(double v1, double q1, double v2, double q2, double v3, double q3) {
        double totalWeight = q1 + q2 + q3;
        if (totalWeight == 0) return v1;
        return (v1 * q1 + v2 * q2 + v3 * q3) / totalWeight;
    }

    public Map<String, Object> evaluateAlert(Map<String, Object> weatherData) {
        List<String> warnings = new ArrayList<>();
        double wind = getDouble(weatherData, "wind_speed");
        double gust = getDouble(weatherData, "wind_gust");
        double vis = getDouble(weatherData, "visibility");
        double turbulence = getDouble(weatherData, "turbulence");
        
        if (wind > WIND_SPEED_THRESHOLD) warnings.add("风速告警: " + String.format("%.1f", wind) + "m/s");
        if (gust > WIND_GUST_THRESHOLD) warnings.add("阵风告警: " + String.format("%.1f", gust) + "m/s");
        if (vis < VISIBILITY_MIN) warnings.add("能见度过低: " + String.format("%.1f", vis) + "km");
        if (turbulence > TURBULENCE_THRESHOLD) warnings.add("湍流告警: " + String.format("%.2f", turbulence));
        
        String level = "NORMAL";
        if (warnings.size() >= 3) level = "CRITICAL";
        else if (warnings.size() >= 2) level = "HIGH";
        else if (warnings.size() == 1) level = "MEDIUM";
        
        return Map.of("has_alert", !warnings.isEmpty(), "warnings", warnings, "level", level);
    }

    private Map<String, Object> evaluateAlertInternal(String droneId, WeatherData w) {
        List<String> warnings = new ArrayList<>();
        if (w.getWindSpeed() > WIND_SPEED_THRESHOLD) warnings.add("风速告警: " + String.format("%.1f", w.getWindSpeed()) + "m/s");
        if (w.getWindGust() > WIND_GUST_THRESHOLD) warnings.add("阵风告警: " + String.format("%.1f", w.getWindGust()) + "m/s");
        if (w.getVisibility() < VISIBILITY_MIN) warnings.add("能见度过低: " + String.format("%.1f", w.getVisibility()) + "km");
        if (w.getTurbulence() > TURBULENCE_THRESHOLD) warnings.add("湍流告警: " + String.format("%.2f", w.getTurbulence()));
        if (warnings.isEmpty()) return null;
        
        String level = warnings.size() >= 3 ? "CRITICAL" : (warnings.size() >= 2 ? "HIGH" : "MEDIUM");
        return Map.of("drone_id", droneId, "timestamp", Instant.now().toEpochMilli(),
                "warnings", warnings, "level", level);
    }

    public List<Map<String, Object>> getDroneAlerts(String droneId) {
        return alertHistory.getOrDefault(droneId, List.of());
    }

    public List<Map<String, Object>> listDataSources() {
        return dataSources;
    }

    /**
     * 定时采集 WRF 模型数据
     */
    public void collectWrfData() {
        log.info("Collecting WRF model data...");
        String wrfUrl = "http://wrf-processor:8081/api/wrf/latest";
        try {
            String response = restTemplate.getForObject(wrfUrl, String.class);
            if (response != null) {
                Map<String, Object> wrfData = objectMapper.readValue(response, new TypeReference<Map<String, Object>>() {});
                Map<String, Object> mappedData = mapWrfResponse(wrfData);
                collect("wrf", mappedData, 0.85);
                updateDataSourceStatus("wrf", "online");
                log.info("WRF数据采集成功");
            }
        } catch (Exception e) {
            log.error("WRF数据采集失败: {}", e.getMessage());
            updateDataSourceStatus("wrf", "offline");
        }
    }

    private Map<String, Object> mapWrfResponse(Map<String, Object> wrfData) {
        Map<String, Object> mapped = new HashMap<>();
        mapped.put("drone_id", "wrf_global");
        mapped.put("latitude", wrfData.getOrDefault("latitude", 0.0));
        mapped.put("longitude", wrfData.getOrDefault("longitude", 0.0));
        mapped.put("altitude", wrfData.getOrDefault("altitude", 0.0));
        mapped.put("temperature", wrfData.getOrDefault("temperature", 0.0));
        mapped.put("humidity", wrfData.getOrDefault("humidity", 0.0));
        mapped.put("wind_speed", wrfData.getOrDefault("wind_speed", 0.0));
        mapped.put("wind_direction", wrfData.getOrDefault("wind_direction", 0.0));
        mapped.put("wind_gust", wrfData.getOrDefault("wind_gust", 0.0));
        mapped.put("pressure", wrfData.getOrDefault("pressure", 0.0));
        mapped.put("visibility", wrfData.getOrDefault("visibility", 10.0));
        mapped.put("turbulence", wrfData.getOrDefault("turbulence", 0.0));
        mapped.put("precipitation", wrfData.getOrDefault("precipitation", 0.0));
        return mapped;
    }

    /**
     * 定时采集地面气象站数据
     */
    public void collectGroundStationData() {
        log.info("Collecting ground station data...");
        String groundUrl = "http://meteor-forecast:8082/api/forecast/ground-stations";
        try {
            String response = restTemplate.getForObject(groundUrl, String.class);
            if (response != null) {
                List<Map<String, Object>> stations = objectMapper.readValue(response, new TypeReference<List<Map<String, Object>>>() {});
                for (Map<String, Object> station : stations) {
                    Map<String, Object> mappedData = mapGroundStationResponse(station);
                    collect("ground_station", mappedData, 0.9);
                }
                updateDataSourceStatus("ground_station", "online");
                log.info("地面气象站数据采集成功: {} 个站点", stations.size());
            }
        } catch (Exception e) {
            log.error("地面气象站数据采集失败: {}", e.getMessage());
            updateDataSourceStatus("ground_station", "offline");
        }
    }

    private Map<String, Object> mapGroundStationResponse(Map<String, Object> station) {
        Map<String, Object> mapped = new HashMap<>();
        mapped.put("drone_id", "ground_" + station.getOrDefault("id", "unknown"));
        mapped.put("latitude", station.getOrDefault("latitude", 0.0));
        mapped.put("longitude", station.getOrDefault("longitude", 0.0));
        mapped.put("altitude", station.getOrDefault("altitude", 0.0));
        mapped.put("temperature", station.getOrDefault("temperature", 0.0));
        mapped.put("humidity", station.getOrDefault("humidity", 0.0));
        mapped.put("wind_speed", station.getOrDefault("wind_speed", 0.0));
        mapped.put("wind_direction", station.getOrDefault("wind_direction", 0.0));
        mapped.put("wind_gust", station.getOrDefault("wind_gust", 0.0));
        mapped.put("pressure", station.getOrDefault("pressure", 0.0));
        mapped.put("visibility", station.getOrDefault("visibility", 10.0));
        mapped.put("turbulence", station.getOrDefault("turbulence", 0.0));
        mapped.put("precipitation", station.getOrDefault("precipitation", 0.0));
        return mapped;
    }

    /**
     * 多源数据融合
     */
    public void fuseMultiSourceData() {
        log.info("Fusing multi-source weather data...");
        String assimilationUrl = "http://data-assimilation:8084/api/assimilation/fuse";
        
        for (String droneId : droneWeatherBuffer.keySet()) {
            try {
                Map<String, Object> request = buildFusionRequest(droneId);
                String response = restTemplate.postForObject(assimilationUrl, request, String.class);
                if (response != null) {
                    Map<String, Object> fusedResult = objectMapper.readValue(response, new TypeReference<Map<String, Object>>() {});
                    processFusionResult(droneId, fusedResult);
                    log.info("数据融合成功: drone={}", droneId);
                }
            } catch (Exception e) {
                log.warn("数据融合失败 for drone {}: {}", droneId, e.getMessage());
                fallbackFusion(droneId);
            }
        }
    }

    private Map<String, Object> buildFusionRequest(String droneId) {
        Deque<WeatherData> buffer = droneWeatherBuffer.get(droneId);
        List<Map<String, Object>> observations = buffer != null ? 
                buffer.stream().map(WeatherData::toMap).collect(Collectors.toList()) : List.of();
        
        return Map.of(
                "drone_id", droneId,
                "observations", observations,
                "algorithm", "ensemble",
                "timestamp", Instant.now().toEpochMilli()
        );
    }

    private void processFusionResult(String droneId, Map<String, Object> result) {
        Map<String, Object> fusedData = new HashMap<>();
        fusedData.put("drone_id", droneId);
        fusedData.put("latitude", result.getOrDefault("latitude", 0.0));
        fusedData.put("longitude", result.getOrDefault("longitude", 0.0));
        fusedData.put("temperature", result.getOrDefault("temperature", 0.0));
        fusedData.put("humidity", result.getOrDefault("humidity", 0.0));
        fusedData.put("wind_speed", result.getOrDefault("wind_speed", 0.0));
        fusedData.put("wind_direction", result.getOrDefault("wind_direction", 0.0));
        fusedData.put("visibility", result.getOrDefault("visibility", 10.0));
        fusedData.put("turbulence", result.getOrDefault("turbulence", 0.0));
        
        collect("fused", fusedData, 0.95);
    }

    private void fallbackFusion(String droneId) {
        Map<String, Object> fused = getFusedWeather(droneId);
        if ((Boolean) fused.getOrDefault("success", false)) {
            Map<String, Object> fusedData = new HashMap<>();
            fusedData.put("drone_id", droneId);
            fusedData.put("wind_speed", fused.get("wind_speed"));
            fusedData.put("temperature", fused.get("temperature"));
            fusedData.put("humidity", fused.get("humidity"));
            fusedData.put("visibility", fused.get("visibility"));
            collect("fused_local", fusedData, 0.85);
            log.info("本地融合完成: drone={}", droneId);
        }
    }

    /**
     * 气象风险评估
     */
    @SuppressWarnings("unchecked")
    public void assessWeatherRisk() {
        log.info("Assessing weather risk...");
        
        for (String droneId : droneWeatherBuffer.keySet()) {
            Map<String, Object> current = getCurrentWeather(droneId);
            if ((Boolean) current.getOrDefault("success", false)) {
                Map<String, Object> weatherData = (Map<String, Object>) current.get("data");
                Map<String, Object> alert = evaluateAlert(weatherData);
                
                if ((Boolean) alert.getOrDefault("has_alert", false)) {
                    List<String> warnings = (List<String>) alert.get("warnings");
                    String level = (String) alert.get("level");
                    
                    log.warn("气象风险告警 - drone={}, level={}, warnings={}", droneId, level, warnings);
                    
                    if ("CRITICAL".equals(level)) {
                        triggerEmergencyAlert(droneId, warnings);
                    } else if ("HIGH".equals(level)) {
                        triggerHighAlert(droneId, warnings);
                    }
                }
            }
        }
    }

    private void triggerEmergencyAlert(String droneId, List<String> warnings) {
        String alertMsg = "无人机 " + droneId + " 紧急告警: " + String.join("; ", warnings);
        log.error("EMERGENCY: {}", alertMsg);
        
        try {
            Map<String, Object> alertRequest = Map.of(
                    "drone_id", droneId,
                    "level", "CRITICAL",
                    "message", alertMsg,
                    "timestamp", Instant.now().toEpochMilli(),
                    "warnings", warnings
            );
            restTemplate.postForObject("http://uav-platform:8080/api/alerts/emergency", alertRequest, String.class);
            log.info("紧急告警已发送到平台");
        } catch (Exception e) {
            log.error("发送紧急告警失败: {}", e.getMessage());
        }
    }

    private void triggerHighAlert(String droneId, List<String> warnings) {
        String alertMsg = "无人机 " + droneId + " 高风险告警: " + String.join("; ", warnings);
        log.warn("HIGH ALERT: {}", alertMsg);
        
        try {
            Map<String, Object> alertRequest = Map.of(
                    "drone_id", droneId,
                    "level", "HIGH",
                    "message", alertMsg,
                    "timestamp", Instant.now().toEpochMilli(),
                    "warnings", warnings
            );
            restTemplate.postForObject("http://uav-platform:8080/api/alerts", alertRequest, String.class);
            log.info("高风险告警已发送到平台");
        } catch (Exception e) {
            log.error("发送告警失败: {}", e.getMessage());
        }
    }

    private void updateDataSourceStatus(String sourceId, String status) {
        for (int i = 0; i < dataSources.size(); i++) {
            Map<String, Object> source = dataSources.get(i);
            if (sourceId.equals(source.get("id"))) {
                Map<String, Object> updated = new HashMap<>(source);
                updated.put("status", status);
                dataSources.set(i, updated);
                break;
            }
        }
    }

    private double getDouble(Map<String, Object> map, String key) {
        Object val = map.get(key);
        if (val instanceof Number) return ((Number) val).doubleValue();
        return 0.0;
    }
}

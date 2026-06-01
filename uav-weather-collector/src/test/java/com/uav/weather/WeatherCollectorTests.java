package com.uav.weather;

import com.uav.weather.controller.WeatherController;
import com.uav.weather.model.WeatherData;
import com.uav.weather.service.WeatherCollectorService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("WeatherCollector 集成测试")
class WeatherCollectorTests {

    private WeatherController weatherController;
    private WeatherCollectorService weatherCollectorService;

    @BeforeEach
    void setUp() {
        weatherController = new WeatherController();
        weatherCollectorService = new WeatherCollectorService();
        ReflectionTestUtils.setField(weatherController, "weatherCollectorService", weatherCollectorService);
    }

    @Test
    @DisplayName("应用上下文加载")
    void testApplicationStartup() {
        assertNotNull(weatherController);
        assertNotNull(weatherCollectorService);
    }

    @Test
    @DisplayName("WeatherData模型创建与toMap")
    void testWeatherDataModel() {
        WeatherData data = new WeatherData();
        data.setSource("wrf");
        data.setDroneId("UAV001");
        data.setTimestamp(System.currentTimeMillis());
        data.setLatitude(39.9);
        data.setLongitude(116.4);

        Map<String, Object> map = data.toMap();
        assertNotNull(map);
        assertEquals("wrf", map.get("source"));
        assertEquals("UAV001", map.get("drone_id"));
    }

    @Test
    @DisplayName("获取无人机气象数据")
    void testGetDroneWeather() {
        Map<String, Object> result = weatherController.getDroneWeather("UAV001");
        assertNotNull(result);
    }

    @Test
    @DisplayName("获取无人机气象历史")
    void testGetDroneWeatherHistory() {
        List<Map<String, Object>> result = weatherController.getDroneWeatherHistory("UAV001", 60);
        assertNotNull(result);
    }

    @Test
    @DisplayName("获取融合气象数据")
    void testGetFusedWeather() {
        Map<String, Object> result = weatherController.getFusedWeather("UAV001");
        assertNotNull(result);
    }

    @Test
    @DisplayName("获取可用数据源列表")
    void testGetAvailableSources() {
        List<Map<String, Object>> result = weatherController.getAvailableSources();
        assertNotNull(result);
    }

    @Test
    @DisplayName("获取告警列表")
    void testGetAlerts() {
        List<Map<String, Object>> result = weatherController.getAlerts("UAV001");
        assertNotNull(result);
    }
}

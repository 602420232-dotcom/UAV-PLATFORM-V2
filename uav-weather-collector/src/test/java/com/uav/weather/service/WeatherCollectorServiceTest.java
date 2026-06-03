package com.uav.weather.service;

import com.uav.weather.config.WeatherProperties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("WeatherCollectorService 单元测试")
class WeatherCollectorServiceTest {

    private WeatherCollectorService service;

    @BeforeEach
    void setUp() {
        service = new WeatherCollectorService(new RestTemplate(), new WeatherProperties());
        service.init();
    }

    @Nested
    @DisplayName("init")
    class InitTests {
        @Test
        @DisplayName("初始化5个数据源")
        void shouldHaveFiveDataSourcesAfterInit() {
            assertEquals(5, service.listDataSources().size());
        }

        @Test
        @DisplayName("包含wrf模型数据源")
        void shouldIncludeWrfSource() {
            assertTrue(service.listDataSources().stream().anyMatch(s -> "wrf".equals(s.get("id"))));
        }
    }

    @Nested
    @DisplayName("evaluateAlert")
    class EvaluateAlertTests {
        @Test
        @DisplayName("正常风速不触发告警")
        void shouldNotAlertForNormalWind() {
            Map<String, Object> data = Map.of("wind_speed", 5.0, "wind_gust", 8.0, "visibility", 10.0);
            Map<String, Object> result = service.evaluateAlert(data);
            assertFalse((Boolean) result.get("has_alert"));
        }

        @Test
        @DisplayName("高风速触发告警")
        void shouldAlertForHighWind() {
            Map<String, Object> data = Map.of("wind_speed", 15.0, "wind_gust", 10.0, "visibility", 10.0);
            Map<String, Object> result = service.evaluateAlert(data);
            assertTrue((Boolean) result.get("has_alert"));
        }

        @Test
        @DisplayName("低能见度触发告警")
        void shouldAlertForLowVisibility() {
            Map<String, Object> data = Map.of("wind_speed", 5.0, "wind_gust", 5.0, "visibility", 1.0);
            Map<String, Object> result = service.evaluateAlert(data);
            assertTrue((Boolean) result.get("has_alert"));
        }

        @Test
        @DisplayName("双重告警为HIGH级别")
        void shouldBeHighWhenMultipleWarnings() {
            Map<String, Object> data = Map.of("wind_speed", 15.0, "wind_gust", 5.0, "visibility", 1.0);
            Map<String, Object> result = service.evaluateAlert(data);
            assertEquals("HIGH", result.get("level"));
        }

        @Test
        @DisplayName("无数据不抛异常")
        void shouldNotThrowOnEmptyData() {
            assertDoesNotThrow(() -> service.evaluateAlert(Map.of()));
        }
    }

    @Nested
    @DisplayName("collectFromUAVSensor")
    class CollectFromUAVSensorTests {
        @Test
        @DisplayName("成功采集返回success")
        void shouldReturnSuccess() {
            Map<String, Object> data = Map.of(
                "drone_id", "UAV001",
                "latitude", 39.9, "longitude", 116.4,
                "altitude", 100.0, "temperature", 22.5
            );
            Map<String, Object> result = service.collectFromUAVSensor(data);
            assertEquals(true, result.get("success"));
            assertEquals("UAV001", result.get("drone_id"));
        }
    }

    @Nested
    @DisplayName("getCurrentWeather")
    class GetCurrentWeatherTests {
        @Test
        @DisplayName("无数据返回false")
        void shouldReturnFalseForUnknownDrone() {
            Map<String, Object> result = service.getCurrentWeather("unknown");
            assertEquals(false, result.get("success"));
        }
    }

    @Nested
    @DisplayName("getWeatherHistory")
    class GetWeatherHistoryTests {
        @Test
        @DisplayName("无数据返回空列表")
        void shouldReturnEmptyListForUnknownDrone() {
            List<Map<String, Object>> result = service.getWeatherHistory("unknown", 60);
            assertTrue(result.isEmpty());
        }
    }

    @Nested
    @DisplayName("getFusedWeather")
    class GetFusedWeatherTests {
        @Test
        @DisplayName("无数据返回false")
        void shouldReturnFalseForUnknownDrone() {
            Map<String, Object> result = service.getFusedWeather("unknown");
            assertEquals(false, result.get("success"));
        }
    }

    @Nested
    @DisplayName("listDataSources")
    class ListDataSourcesTests {
        @Test
        @DisplayName("返回5个数据源")
        void shouldReturnFiveSources() {
            assertEquals(5, service.listDataSources().size());
        }

        @Test
        @DisplayName("每个数据源包含id/name/type/status")
        void shouldContainRequiredFields() {
            List<Map<String, Object>> sources = service.listDataSources();
            for (Map<String, Object> s : sources) {
                assertNotNull(s.get("id"));
                assertNotNull(s.get("name"));
                assertNotNull(s.get("type"));
                assertNotNull(s.get("status"));
            }
        }
    }

    @Nested
    @DisplayName("getDroneAlerts")
    class GetDroneAlertsTests {
        @Test
        @DisplayName("无告警返回空列表")
        void shouldReturnEmptyAlertsInitially() {
            assertTrue(service.getDroneAlerts("UAV001").isEmpty());
        }
    }
}

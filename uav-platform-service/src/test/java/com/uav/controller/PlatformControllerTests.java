package com.uav.controller;

import com.uav.platform.controller.PlatformController;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@DisplayName("PlatformController 单元测试")
class PlatformControllerTest {

    private PlatformController controller;
    private RestTemplate restTemplate;

    @BeforeEach
    void setUp() {
        restTemplate = mock(RestTemplate.class);
        controller = new PlatformController();
        ReflectionTestUtils.setField(controller, "restTemplate", restTemplate);
        ReflectionTestUtils.setField(controller, "wrfProcessorUrl", "http://wrf:8081/api/wrf");
        ReflectionTestUtils.setField(controller, "dataAssimilationUrl", "http://assim:8084/api/assim");
        ReflectionTestUtils.setField(controller, "meteorForecastUrl", "http://meteor:8082/api/forecast");
        ReflectionTestUtils.setField(controller, "pathPlanningUrl", "http://plan:8083/api/plan");
    }

    @Test
    @DisplayName("getWeather 返回成功响应")
    void testGetWeather() {
        when(restTemplate.getForObject(anyString(), eq(Map.class), (Object[]) any()))
                .thenReturn(Map.of("success", true, "data", Map.of()));

        Map<String, Object> result = controller.getWeather("test-file-id");
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("manageTask 返回成功响应")
    void testManageTask() {
        Map<String, Object> result = controller.manageTask(Map.of("action", "start"));
        assertTrue((Boolean) result.get("success"));
        assertEquals("任务管理成功", result.get("message"));
    }

    @Test
    @DisplayName("getDrones 返回成功响应")
    void testGetDrones() {
        Map<String, Object> result = controller.getDrones();
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
    }

    @Test
    @DisplayName("plan 在无 weatherData 时返回错误")
    void testPlanWithoutWeatherData() {
        Map<String, Object> request = Map.of("drones", Map.of(), "tasks", Map.of());
        when(restTemplate.postForObject(anyString(), any(), eq(Map.class)))
                .thenReturn(Map.of("success", false, "error", "service unavailable"));

        Map<String, Object> result = controller.plan(request);
        assertFalse((Boolean) result.get("success"));
    }
}

package com.uav.controller;

import com.uav.common.feign.DataAssimilationClient;
import com.uav.common.feign.MeteorForecastClient;
import com.uav.common.feign.PathPlanningClient;
import com.uav.common.feign.WrfProcessorClient;
import com.uav.platform.controller.PlatformController;
import com.uav.platform.dto.PlanRequest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;


import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@DisplayName("PlatformController 单元测试")
class PlatformControllerTests {

    private PlatformController controller;
    private WrfProcessorClient wrfProcessorClient;
    private DataAssimilationClient dataAssimilationClient;
    private MeteorForecastClient meteorForecastClient;
    private PathPlanningClient pathPlanningClient;

    @BeforeEach
    void setUp() {
        wrfProcessorClient = mock(WrfProcessorClient.class);
        dataAssimilationClient = mock(DataAssimilationClient.class);
        meteorForecastClient = mock(MeteorForecastClient.class);
        pathPlanningClient = mock(PathPlanningClient.class);

        controller = new PlatformController(
                wrfProcessorClient,
                dataAssimilationClient,
                meteorForecastClient,
                pathPlanningClient
        );
    }

    @Test
    @DisplayName("getDrones 返回成功响应")
    void testGetDrones() {
        Map<String, Object> result = controller.getDrones();

        assertNotNull(result.get("data"));
        assertEquals(200, result.get("code"));
    }

    @Test
    @DisplayName("healthCheck 返回服务健康状态")
    void testHealthCheck() {
        when(wrfProcessorClient.health()).thenReturn(Map.of("status", "UP"));
        when(dataAssimilationClient.health()).thenReturn(Map.of("status", "UP"));
        when(meteorForecastClient.health()).thenReturn(Map.of("status", "UP"));
        when(pathPlanningClient.health()).thenReturn(Map.of("status", "UP"));

        Map<String, Object> result = controller.healthCheck();

        assertEquals("UP", result.get("status"));
    }

    @Test
    @DisplayName("plan 综合路径规划成功")
    void testPlanSuccess() {
        PlanRequest request = new PlanRequest();
        request.setDrones(Map.of("id", "drone1"));
        request.setTasks(Map.of("id", "task1"));
        request.setWeatherData(Map.of("temperature", 25.0));
        request.setObstacles(Map.of());
        request.setNoFlyZones(Map.of());

        when(wrfProcessorClient.parseWrfData(any(Map.class))).thenReturn(Map.of("success", true, "data", Map.of()));
        when(dataAssimilationClient.executeAssimilation(any())).thenReturn(Map.of("success", true, "data", Map.of()));
        when(meteorForecastClient.getDetailedForecast(any())).thenReturn(Map.of("success", true, "data", Map.of()));
        when(pathPlanningClient.planFull(any())).thenReturn(Map.of("success", true, "data", Map.of()));

        Map<String, Object> result = controller.plan(request);

        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
    }

    @Test
    @DisplayName("getWeather 返回天气数据")
    void testGetWeather() {
        when(wrfProcessorClient.getWeatherData(anyString())).thenReturn(Map.of("success", true, "code", 200, "data", Map.of()));

        Map<String, Object> result = controller.getWeather("1");

        assertNotNull(result);
        assertEquals(200, result.get("code"));
    }
}

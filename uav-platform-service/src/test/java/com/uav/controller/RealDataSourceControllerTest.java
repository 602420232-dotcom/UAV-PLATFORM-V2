package com.uav.controller;

import com.uav.service.RealDataSourceService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.ResponseEntity;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("RealDataSourceController 单元测试")
class RealDataSourceControllerTest {

    @Mock
    private RealDataSourceService realDataSourceService;

    @InjectMocks
    private RealDataSourceController controller;

    @Nested
    @DisplayName("GET /api/v1/real-data/ground-station")
    class GetGroundStationDataTests {
        @Test
        @DisplayName("返回地面站数据")
        void shouldReturnGroundStationData() {
            List<Map<String, Object>> data = List.of(
                Map.of("id", "GS001", "temperature", 22.5)
            );
            when(realDataSourceService.getGroundStationData()).thenReturn(data);

            ResponseEntity<Map<String, Object>> response = controller.getGroundStationData();

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(200, response.getBody().get("code"));
            assertEquals(data, response.getBody().get("data"));
        }

        @Test
        @DisplayName("空数据返回200")
        void shouldReturn200ForEmptyData() {
            when(realDataSourceService.getGroundStationData()).thenReturn(List.of());

            ResponseEntity<Map<String, Object>> response = controller.getGroundStationData();

            assertEquals(200, response.getStatusCodeValue());
        }
    }

    @Nested
    @DisplayName("GET /api/v1/real-data/buoy")
    class GetBuoyDataTests {
        @Test
        @DisplayName("返回浮标数据")
        void shouldReturnBuoyData() {
            List<Map<String, Object>> data = List.of(
                Map.of("id", "B001", "temperature", 20.5)
            );
            when(realDataSourceService.getBuoyData()).thenReturn(data);

            ResponseEntity<Map<String, Object>> response = controller.getBuoyData();

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(data, response.getBody().get("data"));
        }
    }

    @Nested
    @DisplayName("GET /api/v1/real-data/status")
    class GetDataSourceStatusTests {
        @Test
        @DisplayName("返回数据源状态")
        void shouldReturnDataSourceStatus() {
            Map<String, Object> status = Map.of(
                "ground_station", Map.of("count", 2, "status", "active")
            );
            when(realDataSourceService.getDataSourceStatus()).thenReturn(status);

            ResponseEntity<Map<String, Object>> response = controller.getDataSourceStatus();

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(status, response.getBody().get("data"));
        }

        @Test
        @DisplayName("响应包含code和message字段")
        void shouldContainCodeAndMessage() {
            when(realDataSourceService.getDataSourceStatus()).thenReturn(Map.of());

            ResponseEntity<Map<String, Object>> response = controller.getDataSourceStatus();

            assertNotNull(response.getBody().get("code"));
            assertNotNull(response.getBody().get("message"));
        }
    }

    @Nested
    @DisplayName("响应格式验证")
    class ResponseFormatTests {
        @Test
        @DisplayName("所有端点响应均为200")
        void shouldReturn200ForAllEndpoints() {
            when(realDataSourceService.getGroundStationData()).thenReturn(List.of());
            when(realDataSourceService.getBuoyData()).thenReturn(List.of());
            when(realDataSourceService.getDataSourceStatus()).thenReturn(Map.of());

            assertEquals(200, controller.getGroundStationData().getStatusCodeValue());
            assertEquals(200, controller.getBuoyData().getStatusCodeValue());
            assertEquals(200, controller.getDataSourceStatus().getStatusCodeValue());
        }
    }
}

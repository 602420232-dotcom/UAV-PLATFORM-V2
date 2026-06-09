package com.uav.groundstation.weather;

import com.uav.groundstation.weather.controller.GroundStationController;
import com.uav.groundstation.weather.model.GroundStationData;
import com.uav.groundstation.weather.repository.GroundStationDataRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * 地面气象站服务单元测试
 */
@SuppressWarnings("null")
@ExtendWith(MockitoExtension.class)
class GroundStationControllerTest {

    @Mock
    private GroundStationDataRepository repository;

    private GroundStationController controller;

    private GroundStationData sampleStationData;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        controller = new GroundStationController(repository);

        sampleStationData = GroundStationData.builder()
                .id(1L)
                .stationId("STATION001")
                .stationName("测试气象站")
                .longitude(121.5)
                .latitude(31.2)
                .altitude(100.0)
                .windSpeed(3.0)
                .windDirection(90.0)
                .temperature(28.0)
                .pressure(1015.0)
                .humidity(65.0)
                .precipitation(0.0)
                .visibility(10.0)
                .collectTime(LocalDateTime.now())
                .build();
    }

    @Test
    void getStationData_WithStationId_ReturnsData() {
        when(repository.findLatestByStationId("STATION001")).thenReturn(Optional.of(sampleStationData));

        ResponseEntity<Map<String, Object>> response = controller.getStationData("STATION001");
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        verify(repository).findLatestByStationId("STATION001");
    }

    @Test
    void getStationData_WithInvalidStationId_ReturnsNotFound() {
        when(repository.findLatestByStationId("INVALID")).thenReturn(Optional.empty());

        ResponseEntity<Map<String, Object>> response = controller.getStationData("INVALID");
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(false, result.get("success"));
        assertEquals("站点数据不存在: INVALID", result.get("message"));
    }

    @Test
    void getStationData_WithoutStationId_ReturnsAllData() {
        when(repository.findAll()).thenReturn(List.of(sampleStationData));

        ResponseEntity<Map<String, Object>> response = controller.getStationData(null);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals(1, result.get("total"));
        verify(repository).findAll();
    }

    @Test
    void listStations_ReturnsPagedResults() {
        Page<GroundStationData> page = new PageImpl<>(List.of(sampleStationData));
        when(repository.findAll(any(PageRequest.class))).thenReturn(page);

        ResponseEntity<Map<String, Object>> response = controller.listStations(1, 10);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals(1, ((List<?>) result.get("data")).size());
    }

    @Test
    void getStationDetail_WithValidId_ReturnsData() {
        when(repository.findById(1L)).thenReturn(Optional.of(sampleStationData));

        ResponseEntity<Map<String, Object>> response = controller.getStationDetail(1L);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals("STATION001", ((GroundStationData) result.get("data")).getStationId());
    }

    @Test
    void getStationDetail_WithInvalidId_ReturnsNotFound() {
        when(repository.findById(999L)).thenReturn(Optional.empty());

        ResponseEntity<Map<String, Object>> response = controller.getStationDetail(999L);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(false, result.get("success"));
        assertEquals("气象站数据不存在: id=999", result.get("message"));
    }

    @Test
    void getRealtimeData_WithValidStationId_ReturnsData() {
        when(repository.findLatestByStationId("STATION001")).thenReturn(Optional.of(sampleStationData));

        ResponseEntity<Map<String, Object>> response = controller.getRealtimeData("STATION001");
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertNotNull(result.get("collectTime"));
    }

    @Test
    void getRealtimeData_WithInvalidStationId_ReturnsNotFound() {
        when(repository.findLatestByStationId("INVALID")).thenReturn(Optional.empty());

        ResponseEntity<Map<String, Object>> response = controller.getRealtimeData("INVALID");
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(false, result.get("success"));
        assertEquals("暂无实时数据: INVALID", result.get("message"));
    }

    @Test
    void uploadStationData_ValidData_ReturnsSuccess() {
        when(repository.save(any(GroundStationData.class))).thenReturn(sampleStationData);

        Map<String, Object> request = Map.of(
                "stationId", "STATION001",
                "stationName", "测试气象站",
                "longitude", 121.5,
                "latitude", 31.2,
                "temperature", 28.0
        );

        ResponseEntity<Map<String, Object>> response = controller.uploadStationData(request);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals("数据上传成功", result.get("message"));
        assertEquals(1L, result.get("id"));
        verify(repository).save(any(GroundStationData.class));
    }
}

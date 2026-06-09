package com.uav.buoy.weather;

import com.uav.buoy.weather.controller.BuoyController;
import com.uav.buoy.weather.model.BuoyData;
import com.uav.buoy.weather.repository.BuoyDataRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * 浮标气象服务单元测试
 */
@SuppressWarnings("null")
@ExtendWith(MockitoExtension.class)
class BuoyControllerTest {

    @Mock
    private BuoyDataRepository repository;

    private BuoyController controller;

    private BuoyData sampleBuoyData;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        controller = new BuoyController(repository);

        sampleBuoyData = BuoyData.builder()
                .id(1L)
                .buoyId("BUOY001")
                .buoyName("测试浮标")
                .longitude(121.5)
                .latitude(31.2)
                .windSpeed(5.0)
                .windDirection(180.0)
                .temperature(25.0)
                .pressure(1013.0)
                .humidity(80.0)
                .waveHeight(1.5)
                .waterTemperature(22.0)
                .collectTime(LocalDateTime.now())
                .createdAt(LocalDateTime.now())
                .build();
    }

    @Test
    void getBuoyData_WithBuoyId_ReturnsData() {
        when(repository.findLatestByBuoyId("BUOY001")).thenReturn(Optional.of(sampleBuoyData));

        Map<String, Object> result = controller.getBuoyData("BUOY001");

        assertEquals("success", result.get("status"));
        assertEquals("BUOY001", result.get("buoyId"));
        verify(repository).findLatestByBuoyId("BUOY001");
    }

    @Test
    void getBuoyData_WithInvalidBuoyId_ReturnsNotFound() {
        when(repository.findLatestByBuoyId("INVALID")).thenReturn(Optional.empty());

        Map<String, Object> result = controller.getBuoyData("INVALID");

        assertEquals("not_found", result.get("status"));
        verify(repository).findLatestByBuoyId("INVALID");
    }

    @Test
    void listBuoys_ReturnsPagedResults() {
        Page<BuoyData> page = new PageImpl<>(List.of(sampleBuoyData));
        when(repository.findAll(any(PageRequest.class))).thenReturn(page);

        Map<String, Object> result = controller.listBuoys(1, 10);

        assertEquals("success", result.get("status"));
        assertEquals(1, ((List<?>) result.get("content")).size());
        verify(repository).findAll(any(PageRequest.class));
    }

    @Test
    void listBuoys_EmptyDatabase_ReturnsEmptyList() {
        Page<BuoyData> emptyPage = new PageImpl<>(Collections.emptyList());
        when(repository.findAll(any(PageRequest.class))).thenReturn(emptyPage);

        Map<String, Object> result = controller.listBuoys(1, 10);

        assertEquals("success", result.get("status"));
        assertEquals(0, ((List<?>) result.get("content")).size());
    }

    @Test
    void getBuoyDetail_WithValidId_ReturnsData() {
        when(repository.findById(1L)).thenReturn(Optional.of(sampleBuoyData));

        Map<String, Object> result = controller.getBuoyDetail(1L);

        assertEquals("success", result.get("status"));
        assertEquals(1L, result.get("id"));
        verify(repository).findById(1L);
    }

    @Test
    void getBuoyDetail_WithInvalidId_ReturnsNotFound() {
        when(repository.findById(999L)).thenReturn(Optional.empty());

        Map<String, Object> result = controller.getBuoyDetail(999L);

        assertEquals("not_found", result.get("status"));
        verify(repository).findById(999L);
    }

    @Test
    void uploadBuoyData_ValidData_ReturnsSuccess() {
        when(repository.save(any(BuoyData.class))).thenReturn(sampleBuoyData);

        Map<String, Object> request = Map.of(
                "buoyId", "BUOY001",
                "buoyName", "测试浮标",
                "longitude", 121.5,
                "latitude", 31.2,
                "windSpeed", 5.0
        );

        Map<String, Object> result = controller.uploadBuoyData(request);

        assertEquals("success", result.get("status"));
        assertEquals("浮标数据上传成功", result.get("message"));
        verify(repository).save(any(BuoyData.class));
    }

    @Test
    void uploadBuoyData_MissingRequiredField_ReturnsSuccess() {
        when(repository.save(any(BuoyData.class))).thenReturn(sampleBuoyData);

        // 缺少必需字段 buoyId
        Map<String, Object> request = Map.of(
                "buoyName", "测试浮标",
                "longitude", 121.5
        );

        Map<String, Object> result = controller.uploadBuoyData(request);

        assertEquals("success", result.get("status"));
        verify(repository).save(any(BuoyData.class));
    }

    @Test
    void getRealtimeData_WithValidBuoyId_ReturnsRealtimeFlag() {
        when(repository.findLatestByBuoyId("BUOY001")).thenReturn(Optional.of(sampleBuoyData));

        Map<String, Object> result = controller.getRealtimeData("BUOY001");

        assertEquals("success", result.get("status"));
        assertEquals(true, result.get("realtime"));
        verify(repository).findLatestByBuoyId("BUOY001");
    }

    @Test
    void getRealtimeData_WithInvalidBuoyId_ReturnsNotFound() {
        when(repository.findLatestByBuoyId("INVALID")).thenReturn(Optional.empty());

        Map<String, Object> result = controller.getRealtimeData("INVALID");

        assertEquals("not_found", result.get("status"));
        verify(repository).findLatestByBuoyId("INVALID");
    }
}

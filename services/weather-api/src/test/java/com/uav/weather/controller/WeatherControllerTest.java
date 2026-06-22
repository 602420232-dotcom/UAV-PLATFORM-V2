package com.uav.weather.controller;

import com.uav.weather.dto.WeatherQueryRequest;
import com.uav.weather.dto.WindProfileQueryRequest;
import com.uav.weather.entity.WeatherGrid;
import com.uav.weather.entity.WindProfile;
import com.uav.weather.service.WeatherService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

/**
 * Weather 控制器单元测试
 */
@DisplayName("Weather 控制器测试")
@ExtendWith(MockitoExtension.class)
class WeatherControllerTest {

    @Mock
    private WeatherService weatherService;

    @InjectMocks
    private WeatherController weatherController;

    @Test
    @DisplayName("queryPoint 应返回单点气象数据")
    void queryPointShouldReturnWeatherGrid() {
        WeatherGrid grid = new WeatherGrid();
        grid.setId(1L);
        grid.setSource("WRF");
        grid.setLongitude(116.4);
        grid.setLatitude(39.9);
        grid.setAltitude(100.0);
        grid.setTemperature(25.5);
        grid.setWindSpeed(5.2);

        when(weatherService.queryPoint(any(WeatherQueryRequest.class))).thenReturn(grid);

        WeatherQueryRequest request = new WeatherQueryRequest();
        request.setLongitude(116.4);
        request.setLatitude(39.9);
        request.setAltitude(100.0);

        var result = weatherController.queryPoint(request);

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("WRF", result.getData().getSource());
        assertEquals(25.5, result.getData().getTemperature());
    }

    @Test
    @DisplayName("queryRegion 应返回区域气象格点列表")
    void queryRegionShouldReturnWeatherGridList() {
        WeatherGrid grid = new WeatherGrid();
        grid.setId(1L);
        grid.setSource("FENGWU_GHR");
        grid.setLongitude(116.4);
        grid.setLatitude(39.9);

        when(weatherService.queryRegion(anyDouble(), anyDouble(), anyDouble(), anyDouble(),
                any(), any(), any())).thenReturn(List.of(grid));

        var result = weatherController.queryRegion(116.0, 39.0, 117.0, 40.0, null, null, null);

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals(1, result.getData().size());
        assertEquals("FENGWU_GHR", result.getData().get(0).getSource());
    }

    @Test
    @DisplayName("queryWindProfile 应返回风场剖面数据")
    void queryWindProfileShouldReturnWindData() {
        WindProfile profile = new WindProfile();
        profile.setId(1L);
        profile.setSource("FUSION");
        profile.setLongitude(116.4);
        profile.setLatitude(39.9);

        when(weatherService.queryWindProfile(any(WindProfileQueryRequest.class))).thenReturn(profile);

        WindProfileQueryRequest request = new WindProfileQueryRequest();
        request.setLongitude(116.4);
        request.setLatitude(39.9);
        request.setMinAltitude(100.0);
        request.setMaxAltitude(300.0);
        request.setInterval(100.0);

        var result = weatherController.queryWindProfile(request);

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("FUSION", result.getData().getSource());
    }

    @Test
    @DisplayName("queryFusion 应返回多源融合气象数据")
    void queryFusionShouldReturnFusionData() {
        WeatherGrid grid = new WeatherGrid();
        grid.setId(2L);
        grid.setSource("FUSION");
        grid.setTemperature(26.0);

        when(weatherService.queryFusion(any(WeatherQueryRequest.class))).thenReturn(grid);

        WeatherQueryRequest request = new WeatherQueryRequest();
        request.setLongitude(116.4);
        request.setLatitude(39.9);

        var result = weatherController.queryFusion(request);

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("FUSION", result.getData().getSource());
        assertEquals(26.0, result.getData().getTemperature());
    }

    @Test
    @DisplayName("queryRegion 带完整参数应正确传递")
    void queryRegionWithFullParamsShouldPassCorrectly() {
        WeatherGrid grid = new WeatherGrid();
        grid.setId(1L);
        grid.setSource("ECMWF");
        grid.setLongitude(116.5);
        grid.setLatitude(39.5);

        when(weatherService.queryRegion(eq(116.0), eq(39.0), eq(117.0), eq(40.0),
                eq(100.0), eq("ECMWF"), any(LocalDateTime.class))).thenReturn(List.of(grid));

        var result = weatherController.queryRegion(116.0, 39.0, 117.0, 40.0, 100.0, "ECMWF", LocalDateTime.now());

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("ECMWF", result.getData().get(0).getSource());
    }
}

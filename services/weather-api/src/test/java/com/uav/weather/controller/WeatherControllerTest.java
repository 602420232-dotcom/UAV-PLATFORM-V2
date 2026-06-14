package com.uav.weather.controller;

import com.uav.weather.WeatherApplication;
import com.uav.weather.dto.WeatherQueryRequest;
import com.uav.weather.dto.WindProfileQueryRequest;
import com.uav.weather.entity.WeatherGrid;
import com.uav.weather.entity.WindProfile;
import com.uav.weather.service.WeatherService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Weather 控制器单元测试
 */
@DisplayName("Weather 控制器测试")
@SpringBootTest(classes = WeatherApplication.class)
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(locations = "classpath:application-test.yml")
class WeatherControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private WeatherService weatherService;

    @Test
    @DisplayName("POST /api/v1/weather/point 应返回单点气象数据")
    @WithMockUser(roles = {"ADMIN"})
    void queryPointShouldReturnWeatherGrid() throws Exception {
        WeatherGrid grid = new WeatherGrid();
        grid.setId(1L);
        grid.setSource("WRF");
        grid.setLongitude(116.4);
        grid.setLatitude(39.9);
        grid.setAltitude(100.0);
        grid.setTemperature(25.5);
        grid.setWindSpeed(5.2);

        when(weatherService.queryPoint(any(WeatherQueryRequest.class))).thenReturn(grid);

        mockMvc.perform(post("/api/v1/weather/point")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"longitude\":116.4,\"latitude\":39.9,\"altitude\":100.0}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.source").value("WRF"))
                .andExpect(jsonPath("$.data.temperature").value(25.5));
    }

    @Test
    @DisplayName("GET /api/v1/weather/region 应返回区域气象格点列表")
    @WithMockUser(roles = {"ADMIN"})
    void queryRegionShouldReturnWeatherGridList() throws Exception {
        WeatherGrid grid = new WeatherGrid();
        grid.setId(1L);
        grid.setSource("FENGWU_GHR");
        grid.setLongitude(116.4);
        grid.setLatitude(39.9);

        when(weatherService.queryRegion(anyDouble(), anyDouble(), anyDouble(), anyDouble(),
                any(), any(), any())).thenReturn(List.of(grid));

        mockMvc.perform(get("/api/v1/weather/region")
                        .param("minLon", "116.0")
                        .param("minLat", "39.0")
                        .param("maxLon", "117.0")
                        .param("maxLat", "40.0")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].source").value("FENGWU_GHR"));
    }

    @Test
    @DisplayName("POST /api/v1/weather/wind-profile 应返回风场剖面数据")
    @WithMockUser(roles = {"ADMIN"})
    void queryWindProfileShouldReturnWindData() throws Exception {
        WindProfile profile = new WindProfile();
        profile.setId(1L);
        profile.setSource("FUSION");
        profile.setLongitude(116.4);
        profile.setLatitude(39.9);

        when(weatherService.queryWindProfile(any(WindProfileQueryRequest.class))).thenReturn(profile);

        mockMvc.perform(post("/api/v1/weather/wind-profile")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"longitude\":116.4,\"latitude\":39.9,\"minAltitude\":100.0,\"maxAltitude\":300.0,\"interval\":100.0}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.source").value("FUSION"));
    }

    @Test
    @DisplayName("POST /api/v1/weather/fusion 应返回多源融合气象数据")
    @WithMockUser(roles = {"ADMIN"})
    void queryFusionShouldReturnFusionData() throws Exception {
        WeatherGrid grid = new WeatherGrid();
        grid.setId(2L);
        grid.setSource("FUSION");
        grid.setTemperature(26.0);

        when(weatherService.queryFusion(any(WeatherQueryRequest.class))).thenReturn(grid);

        mockMvc.perform(post("/api/v1/weather/fusion")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"longitude\":116.4,\"latitude\":39.9}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.source").value("FUSION"));
    }

    @Test
    @DisplayName("无效请求参数应返回业务错误码 1000")
    @WithMockUser(roles = {"ADMIN"})
    void invalidRequestShouldReturnBadRequest() throws Exception {
        mockMvc.perform(post("/api/v1/weather/point")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(1000));
    }
}

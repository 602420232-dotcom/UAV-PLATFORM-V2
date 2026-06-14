package com.uav.utm.controller;

import com.uav.utm.UtmApplication;
import com.uav.utm.entity.Airspace;
import com.uav.utm.service.AirspaceService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * UTM 控制器单元测试
 */
@DisplayName("UTM 控制器测试")
@SpringBootTest(classes = com.uav.utm.UtmApplication.class)
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(locations = "classpath:application-test.yml")
class UtmControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private AirspaceService airspaceService;

    @Test
    @DisplayName("GET /api/v1/airspaces 应返回空域列表")
    void getAirspacesShouldReturnAirspaceList() throws Exception {
        Airspace airspace = new Airspace();
        airspace.setId(1L);
        airspace.setType(Airspace.AirspaceType.STATIC);
        airspace.setBoundsJson("{\"type\":\"Polygon\"}");
        airspace.setAltitudeMin(0.0);
        airspace.setAltitudeMax(120.0);
        airspace.setStatus(Airspace.AirspaceStatus.ACTIVE);

        when(airspaceService.getAirspaces()).thenReturn(List.of(airspace));

        mockMvc.perform(get("/api/v1/airspaces")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].type").value("STATIC"))
                .andExpect(jsonPath("$.data[0].altitudeMax").value(120.0));
    }

    @Test
    @DisplayName("POST /api/v1/airspaces 应创建动态空域")
    void createAirspaceShouldReturnCreatedAirspace() throws Exception {
        Airspace airspace = new Airspace();
        airspace.setId(1L);
        airspace.setType(Airspace.AirspaceType.DYNAMIC);
        airspace.setBoundsJson("{\"type\":\"Circle\",\"radius\":500}");
        airspace.setAltitudeMin(50.0);
        airspace.setAltitudeMax(200.0);
        airspace.setStatus(Airspace.AirspaceStatus.ACTIVE);

        when(airspaceService.createDynamicAirspace(any(Airspace.class))).thenReturn(airspace);

        mockMvc.perform(post("/api/v1/airspaces")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"type\":\"DYNAMIC\",\"boundsJson\":\"{\\\"type\\\":\\\"Circle\\\",\\\"radius\\\":500}\",\"altitudeMin\":50.0,\"altitudeMax\":200.0,\"status\":\"ACTIVE\"}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.type").value("DYNAMIC"))
                .andExpect(jsonPath("$.data.altitudeMin").value(50.0));
    }

    @Test
    @DisplayName("GET /api/v1/airspaces/check 应返回空域限制检查结果")
    void checkAirspaceRestrictionShouldReturnBoolean() throws Exception {
        when(airspaceService.checkAirspaceRestriction(anyDouble(), anyDouble(), anyDouble()))
                .thenReturn(true);

        mockMvc.perform(get("/api/v1/airspaces/check")
                        .param("lon", "116.4")
                        .param("lat", "39.9")
                        .param("altitude", "100.0")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").value(true));
    }

    @Test
    @DisplayName("GET /api/v1/airspaces/check 坐标在限制区外应返回 false")
    void checkAirspaceOutsideRestrictionShouldReturnFalse() throws Exception {
        when(airspaceService.checkAirspaceRestriction(anyDouble(), anyDouble(), anyDouble()))
                .thenReturn(false);

        mockMvc.perform(get("/api/v1/airspaces/check")
                        .param("lon", "120.0")
                        .param("lat", "35.0")
                        .param("altitude", "500.0")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").value(false));
    }

    @Test
    @DisplayName("创建空域缺少必填字段应返回 400")
    void createAirspaceWithoutRequiredFieldsShouldReturnBadRequest() throws Exception {
        mockMvc.perform(post("/api/v1/airspaces")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"altitudeMin\":50.0}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest());
    }
}

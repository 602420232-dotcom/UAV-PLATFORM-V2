package com.uav.risk.controller;

import com.uav.risk.RiskApplication;
import com.uav.risk.dto.RiskQueryRequest;
import com.uav.risk.entity.RiskAssessment;
import com.uav.risk.service.RiskService;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Risk 控制器单元测试
 */
@DisplayName("Risk 控制器测试")
@SpringBootTest(classes = com.uav.risk.RiskApplication.class)
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(locations = "classpath:application-test.yml")
class RiskControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private RiskService riskService;

    @Test
    @DisplayName("POST /api/v1/risk/assess 应返回风险评估结果")
    void assessShouldReturnRiskAssessment() throws Exception {
        RiskAssessment assessment = new RiskAssessment();
        assessment.setId(1L);
        assessment.setType("COMPOSITE");
        assessment.setLevel(3);
        assessment.setScore(65);

        when(riskService.assessRisk(any(RiskQueryRequest.class))).thenReturn(assessment);

        mockMvc.perform(post("/api/v1/risk/assess")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"longitude\":116.4,\"latitude\":39.9,\"altitude\":100.0}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.type").value("COMPOSITE"))
                .andExpect(jsonPath("$.data.level").value(3))
                .andExpect(jsonPath("$.data.score").value(65));
    }

    @Test
    @DisplayName("GET /api/v1/risk/map 应返回区域风险栅格地图")
    void riskMapShouldReturnGridList() throws Exception {
        RiskAssessment grid1 = new RiskAssessment();
        grid1.setId(1L);
        grid1.setType("WEATHER");
        grid1.setLevel(2);

        RiskAssessment grid2 = new RiskAssessment();
        grid2.setId(2L);
        grid2.setType("AIRSPACE");
        grid2.setLevel(4);

        when(riskService.generateRiskMap(anyDouble(), anyDouble(), anyDouble(), anyDouble(), anyDouble()))
                .thenReturn(List.of(grid1, grid2));

        mockMvc.perform(get("/api/v1/risk/map")
                        .param("minLon", "116.0")
                        .param("minLat", "39.0")
                        .param("maxLon", "117.0")
                        .param("maxLat", "40.0")
                        .param("resolution", "0.01")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.length()").value(2))
                .andExpect(jsonPath("$.data[0].type").value("WEATHER"));
    }

    @Test
    @DisplayName("GET /api/v1/risk/history 应返回历史风险评估记录")
    void historyShouldReturnRiskRecords() throws Exception {
        RiskAssessment record = new RiskAssessment();
        record.setId(1L);
        record.setType("TERRAIN");
        record.setLevel(1);

        when(riskService.getRiskHistory(any(), any(), anyInt())).thenReturn(List.of(record));

        mockMvc.perform(get("/api/v1/risk/history")
                        .param("limit", "5")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].type").value("TERRAIN"));
    }

    @Test
    @DisplayName("GET /api/v1/risk/history 不带参数应使用默认值")
    void historyWithoutParamsShouldUseDefaults() throws Exception {
        when(riskService.getRiskHistory(null, null, 10)).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/risk/history")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    @DisplayName("无效风险评估请求应返回 400")
    void invalidAssessRequestShouldReturnBadRequest() throws Exception {
        mockMvc.perform(post("/api/v1/risk/assess")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest());
    }
}

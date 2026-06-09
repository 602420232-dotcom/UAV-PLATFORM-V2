package com.uav.bayesian.controller;

import com.uav.bayesian.service.AlertService;
import com.uav.bayesian.service.AssimilationService;
import com.uav.bayesian.service.CacheService;
import com.uav.bayesian.service.VarianceFieldService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.ResponseEntity;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@DisplayName("数据同化平台控制器测试")
class DataAssimilationControllerTests {

    @Mock
    private AssimilationService assimilationService;

    @Mock
    private CacheService cacheService;

    @Mock
    private VarianceFieldService varianceFieldService;

    @Mock
    private AlertService alertService;

    private AssimilationController assimilationController;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        assimilationController = new AssimilationController(assimilationService);
    }

    @Test
    @DisplayName("执行同化")
    void testExecuteAssimilation() {
        Map<String, Object> mockResponse = new HashMap<>();
        mockResponse.put("status", "success");
        mockResponse.put("jobId", "test-123");
        when(assimilationService.executeAssimilation(any())).thenReturn(mockResponse);

        ResponseEntity<?> result = assimilationController.execute(new HashMap<>());

        assertNotNull(result);
        Object bodyObj = result.getBody();
        assertNotNull(bodyObj);
        assertTrue(bodyObj instanceof Map);
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) bodyObj;
        assertNotNull(body.get("status"));
        assertEquals("success", body.get("status").toString());
    }

    @Test
    @DisplayName("获取同化状态")
    void testGetStatus() {
        String jobId = "test-job-001";
        Map<String, Object> mockResponse = new HashMap<>();
        mockResponse.put("status", "completed");
        when(assimilationService.getJobStatus(anyString())).thenReturn(mockResponse);

        ResponseEntity<?> result = assimilationController.getStatus(jobId);

        assertNotNull(result);
        Object bodyObj = result.getBody();
        assertNotNull(bodyObj);
        assertTrue(bodyObj instanceof Map);
    }

    @Test
    @DisplayName("计算方差场")
    void testComputeVariance() {
        Map<String, Object> mockResponse = new HashMap<>();
        mockResponse.put("variance", new double[]{1.0, 2.0});
        mockResponse.put("mean", 0.5);
        mockResponse.put("max", 2.0);
        mockResponse.put("min", 0.3);
        when(varianceFieldService.computeVariance(any())).thenReturn(mockResponse);

        ResponseEntity<?> result = varianceFieldController.computeVariance(new HashMap<>());

        assertNotNull(result);
        Object bodyObj = result.getBody();
        assertNotNull(bodyObj);
        assertTrue(bodyObj instanceof Map);
    }

    @Test
    @DisplayName("获取数据源列表")
    void testListSources() {
        ResponseEntity<?> result = dataController.listSources();

        assertNotNull(result);
        Object bodyObj = result.getBody();
        assertNotNull(bodyObj);
        assertTrue(bodyObj instanceof Map);
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) bodyObj;
        assertNotNull(body.get("sources"));
    }

    @Test
    @DisplayName("获取数据服务状态")
    void testDataStatus() {
        ResponseEntity<?> result = dataController.status();

        assertNotNull(result);
        Object bodyObj = result.getBody();
        assertNotNull(bodyObj);
        assertTrue(bodyObj instanceof Map);
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) bodyObj;
        assertNotNull(body.get("status"));
        assertEquals("connected", body.get("status").toString());
    }

    @Test
    @DisplayName("获取弹性状态")
    void testResilienceStatus() {
        ResponseEntity<?> result = resilienceController.status();

        assertNotNull(result);
        Object bodyObj = result.getBody();
        assertNotNull(bodyObj);
        assertTrue(bodyObj instanceof Map);
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) bodyObj;
        assertNotNull(body.get("circuitBreaker"));
        assertEquals("closed", body.get("circuitBreaker").toString());
    }

    @Test
    @DisplayName("测试降级通知")
    void testDegradedNotification() {
        ResponseEntity<?> result = resilienceController.testDegraded();

        assertNotNull(result);
        Object bodyObj = result.getBody();
        assertNotNull(bodyObj);
        assertTrue(bodyObj instanceof Map);
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) bodyObj;
        assertNotNull(body.get("message"));
        assertEquals("降级测试完成", body.get("message").toString());
    }
}

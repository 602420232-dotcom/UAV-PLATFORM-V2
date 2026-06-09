package com.uav.bayesian.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("AssimilationService 单元测试")
class AssimilationServiceTest {

    @Mock
    private PythonService pythonService;

    private AssimilationService service;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        service = new AssimilationService(pythonService);
    }

    @Nested
    @DisplayName("executeAssimilation")
    class ExecuteAssimilationTests {
        @Test
        @DisplayName("成功执行返回completed状态")
        void shouldReturnCompletedOnSuccess() {
            Map<String, Object> request = new HashMap<>();
            request.put("algorithm", "3dvar");
            when(pythonService.executeAssimilation(any())).thenReturn("{\"result\":\"ok\"}");

            Map<String, Object> result = service.executeAssimilation(request);

            assertNotNull(result.get("status"));
            assertEquals("completed", result.get("status").toString());
            assertNotNull(result.get("jobId"));
            assertNotNull(result.get("result"));
            assertEquals("{\"result\":\"ok\"}", result.get("result").toString());
        }

        @Test
        @DisplayName("Python服务失败返回failed状态")
        void shouldReturnFailedOnPythonError() {
            Map<String, Object> request = new HashMap<>();
            request.put("algorithm", "4dvar");
            when(pythonService.executeAssimilation(any())).thenThrow(new RuntimeException("Python error"));

            Map<String, Object> result = service.executeAssimilation(request);

            assertNotNull(result.get("status"));
            assertEquals("failed", result.get("status").toString());
            assertNotNull(result.get("error"));
            assertEquals("同化处理失败", result.get("error").toString());
        }

        @Test
        @DisplayName("每次执行生成唯一jobId")
        void shouldGenerateUniqueJobId() {
            when(pythonService.executeAssimilation(any())).thenReturn("ok");
            Map<String, Object> r1 = service.executeAssimilation(new HashMap<>());
            Map<String, Object> r2 = service.executeAssimilation(new HashMap<>());
            assertNotNull(r1.get("jobId"));
            assertNotNull(r2.get("jobId"));
            assertNotEquals(r1.get("jobId").toString(), r2.get("jobId").toString());
        }
    }

    @Nested
    @DisplayName("getJobStatus")
    class GetJobStatusTests {
        @Test
        @DisplayName("不存在的jobId返回not_found")
        void shouldReturnNotFoundForMissingJobId() {
            Object statusObj = service.getJobStatus("nonexistent");
            assertNotNull(statusObj);
            assertTrue(statusObj instanceof Map, "Status should be a Map");
            @SuppressWarnings("unchecked")
            Map<String, Object> statusMap = (Map<String, Object>) statusObj;
            assertNotNull(statusMap.get("status"));
            assertEquals("not_found", statusMap.get("status").toString());
        }

        @Test
        @DisplayName("已完成的job返回completed状态")
        void shouldReturnCompletedStatus() {
            Map<String, Object> request = new HashMap<>();
            request.put("algorithm", "3dvar");
            when(pythonService.executeAssimilation(any())).thenReturn("ok");
            Map<String, Object> result = service.executeAssimilation(request);
            assertNotNull(result.get("jobId"));
            String jobId = result.get("jobId").toString();

            Object statusObj = service.getJobStatus(jobId);
            assertNotNull(statusObj);
            assertTrue(statusObj instanceof Map, "Status should be a Map");
            @SuppressWarnings("unchecked")
            Map<String, Object> statusMap = (Map<String, Object>) statusObj;
            assertNotNull(statusMap.get("status"));
            assertEquals("completed", statusMap.get("status").toString());
        }

        @Test
        @DisplayName("失败的job保留failed状态")
        void shouldRetainFailedStatus() {
            when(pythonService.executeAssimilation(any())).thenThrow(new RuntimeException("fail"));
            Map<String, Object> result = service.executeAssimilation(new HashMap<>());
            assertNotNull(result.get("jobId"));
            String jobId = result.get("jobId").toString();

            Object statusObj = service.getJobStatus(jobId);
            assertNotNull(statusObj);
            assertTrue(statusObj instanceof Map, "Status should be a Map");
            @SuppressWarnings("unchecked")
            Map<String, Object> statusMap = (Map<String, Object>) statusObj;
            assertNotNull(statusMap.get("status"));
            assertEquals("failed", statusMap.get("status").toString());
        }
    }
}

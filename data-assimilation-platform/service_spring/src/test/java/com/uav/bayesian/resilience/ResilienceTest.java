package com.uav.bayesian.resilience;

import com.uav.bayesian.service.AssimilationService;
import com.uav.bayesian.service.PythonService;
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
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("弹性机制单元测试")
class ResilienceTest {

    @Mock
    private PythonService pythonService;

    private AssimilationService assimilationService;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        assimilationService = new AssimilationService(pythonService);
    }

    @Nested
    @DisplayName("AssimilationService 测试")
    class AssimilationServiceTests {

        @Test
        @DisplayName("成功执行返回completed状态")
        void shouldReturnCompletedOnSuccess() {
            Map<String, Object> request = new HashMap<>();
            request.put("algorithm", "3dvar");
            when(pythonService.executeAssimilation(any())).thenReturn("{\"result\":\"ok\"}");

            Map<String, Object> result = assimilationService.executeAssimilation(request);

            assertNotNull(result);
            assertNotNull(result.get("status"));
            assertEquals("completed", result.get("status").toString());
            assertNotNull(result.get("jobId"));
        }

        @Test
        @DisplayName("Python服务失败返回failed状态")
        void shouldReturnFailedOnPythonError() {
            Map<String, Object> request = new HashMap<>();
            request.put("algorithm", "4dvar");
            when(pythonService.executeAssimilation(any())).thenThrow(new RuntimeException("Python error"));

            Map<String, Object> result = assimilationService.executeAssimilation(request);

            assertNotNull(result);
            assertNotNull(result.get("status"));
            assertEquals("failed", result.get("status").toString());
            assertNotNull(result.get("error"));
        }

        @Test
        @DisplayName("每次执行生成唯一jobId")
        void shouldGenerateUniqueJobId() {
            when(pythonService.executeAssimilation(any())).thenReturn("ok");
            Map<String, Object> r1 = assimilationService.executeAssimilation(new HashMap<>());
            Map<String, Object> r2 = assimilationService.executeAssimilation(new HashMap<>());
            assertNotNull(r1.get("jobId"));
            assertNotNull(r2.get("jobId"));
            assertNotEquals(r1.get("jobId").toString(), r2.get("jobId").toString());
        }

        @Test
        @DisplayName("不存在的jobId返回not_found")
        void shouldReturnNotFoundForMissingJobId() {
            Object result = assimilationService.getJobStatus("nonexistent");
            assertNotNull(result);
            assertTrue(result instanceof Map);
            @SuppressWarnings("unchecked")
            Map<String, Object> statusMap = (Map<String, Object>) result;
            assertNotNull(statusMap.get("status"));
            assertEquals("not_found", statusMap.get("status").toString());
        }
    }
}

package com.uav.bayesian.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("VarianceFieldService 单元测试")
class VarianceFieldServiceTest {

    private VarianceFieldService service;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入（无依赖）
        service = new VarianceFieldService();
    }

    @Test
    @DisplayName("computeVariance 返回成功状态")
    void shouldReturnSuccessStatus() {
        Map<String, Object> result = service.computeVariance(Map.of());
        assertEquals("success", result.get("status"));
    }

    @SuppressWarnings("unchecked")
    @Test
    @DisplayName("computeVariance 包含方差信息")
    void shouldContainVarianceInfo() {
        Map<String, Object> result = service.computeVariance(Map.of("domain", "100x100"));
        assertNotNull(result.get("variance"));
        Map<String, Object> variance = (Map<String, Object>) result.get("variance");
        assertNotNull(variance.get("mean"));
        assertNotNull(variance.get("max"));
        assertNotNull(variance.get("min"));
        assertEquals(0.5, variance.get("mean"));
        assertEquals(1.2, variance.get("max"));
        assertEquals(0.3, variance.get("min"));
    }

    @Test
    @DisplayName("computeVariance 包含完成消息")
    void shouldContainCompletionMessage() {
        Map<String, Object> result = service.computeVariance(Map.of());
        assertEquals("方差场计算完成", result.get("message"));
    }

    @Test
    @DisplayName("null请求不抛异常")
    void shouldNotThrowOnNullRequest() {
        assertDoesNotThrow(() -> service.computeVariance(null));
    }
}

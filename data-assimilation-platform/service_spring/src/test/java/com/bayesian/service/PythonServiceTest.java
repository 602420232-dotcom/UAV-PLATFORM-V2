package com.bayesian.service;

import com.bayesian.client.PythonServiceClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("PythonService 单元测试")
class PythonServiceTest {

    @Mock
    private PythonServiceClient pythonClient;

    @InjectMocks
    private PythonService service;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(service, "pythonServiceUrl", "http://localhost:8000");
    }

    @Nested
    @DisplayName("executeAssimilation")
    class ExecuteAssimilationTests {
        @Test
        @DisplayName("委托给PythonServiceClient")
        void shouldDelegateToClient() {
            Map<String, Object> request = Map.of("algorithm", "3dvar");
            when(pythonClient.executeAssimilation(eq("http://localhost:8000"), eq(request)))
                    .thenReturn("{\"status\":\"ok\"}");

            String result = service.executeAssimilation(request);

            assertEquals("{\"status\":\"ok\"}", result);
            verify(pythonClient).executeAssimilation("http://localhost:8000", request);
        }

        @Test
        @DisplayName("传递null请求不抛异常")
        void shouldNotThrowOnNullRequest() {
            when(pythonClient.executeAssimilation(anyString(), isNull()))
                    .thenReturn("ok");
            assertDoesNotThrow(() -> service.executeAssimilation(null));
        }
    }
}

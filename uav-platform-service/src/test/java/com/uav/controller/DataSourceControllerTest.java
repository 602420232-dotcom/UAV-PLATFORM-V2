package com.uav.controller;

import com.uav.common.exception.DataNotFoundException;
import com.uav.service.DataSourceService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("DataSourceController 单元测试")
class DataSourceControllerTest {

    @Mock
    private DataSourceService dataSourceService;

    @InjectMocks
    private DataSourceController controller;

    private Map<String, Object> sampleSource;

    @BeforeEach
    void setUp() {
        sampleSource = new HashMap<>();
        sampleSource.put("id", 1L);
        sampleSource.put("name", "Test Source");
        sampleSource.put("type", "ground_station");
        sampleSource.put("url", "http://test");
        sampleSource.put("status", "active");
    }

    @Nested
    @DisplayName("GET /api/v1/data-sources")
    class GetDataSourceListTests {
        @Test
        @DisplayName("返回数据源列表成功")
        void shouldReturnDataSourceList() {
            List<Map<String, Object>> sources = List.of(sampleSource);
            when(dataSourceService.listDataSources()).thenReturn(sources);

            ResponseEntity<Map<String, Object>> response = controller.getDataSourceList();

            assertEquals(200, response.getStatusCodeValue());
            Map<String, Object> body = response.getBody();
            assertEquals(200, body.get("code"));
            assertEquals(sources, body.get("data"));
        }

        @Test
        @DisplayName("空列表返回200")
        void shouldReturn200ForEmptyList() {
            when(dataSourceService.listDataSources()).thenReturn(List.of());

            ResponseEntity<Map<String, Object>> response = controller.getDataSourceList();

            assertEquals(200, response.getStatusCodeValue());
        }
    }

    @Nested
    @DisplayName("GET /api/v1/data-sources/{id}")
    class GetDataSourceByIdTests {
        @Test
        @DisplayName("存在的数据源返回详情")
        void shouldReturnSourceForExistingId() {
            when(dataSourceService.getDataSourceById(1L)).thenReturn(sampleSource);

            ResponseEntity<Map<String, Object>> response = controller.getDataSourceById(1L);

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(sampleSource, response.getBody().get("data"));
        }

        @Test
        @DisplayName("不存在的数据源抛出DataNotFoundException")
        void shouldThrowNotFoundForMissingId() {
            when(dataSourceService.getDataSourceById(999L)).thenReturn(null);

            assertThrows(DataNotFoundException.class, () -> controller.getDataSourceById(999L));
        }
    }

    @Nested
    @DisplayName("POST /api/v1/data-sources")
    class CreateDataSourceTests {
        @Test
        @DisplayName("创建成功返回数据")
        void shouldCreateSuccessfully() {
            Map<String, Object> request = Map.of("name", "New", "type", "satellite");
            when(dataSourceService.createDataSource(request)).thenReturn(sampleSource);

            ResponseEntity<Map<String, Object>> response = controller.createDataSource(request);

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(sampleSource, response.getBody().get("data"));
            verify(dataSourceService).createDataSource(request);
        }
    }

    @Nested
    @DisplayName("PUT /api/v1/data-sources/{id}")
    class UpdateDataSourceTests {
        @Test
        @DisplayName("更新成功返回更新后数据")
        void shouldUpdateSuccessfully() {
            Map<String, Object> request = Map.of("name", "Updated");
            when(dataSourceService.updateDataSource(1L, request)).thenReturn(sampleSource);

            ResponseEntity<Map<String, Object>> response = controller.updateDataSource(1L, request);

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(sampleSource, response.getBody().get("data"));
        }

        @Test
        @DisplayName("更新不存在的数据源抛出异常")
        void shouldThrowNotFoundForMissingSource() {
            Map<String, Object> request = Map.of("name", "X");
            when(dataSourceService.updateDataSource(999L, request)).thenReturn(null);

            assertThrows(DataNotFoundException.class, () -> controller.updateDataSource(999L, request));
        }
    }

    @Nested
    @DisplayName("DELETE /api/v1/data-sources/{id}")
    class DeleteDataSourceTests {
        @Test
        @DisplayName("删除成功返回200")
        void shouldDeleteSuccessfully() {
            when(dataSourceService.deleteDataSource(1L)).thenReturn(true);

            ResponseEntity<Map<String, Object>> response = controller.deleteDataSource(1L);

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(200, response.getBody().get("code"));
        }

        @Test
        @DisplayName("删除不存在的数据源抛出异常")
        void shouldThrowNotFoundForMissingSource() {
            when(dataSourceService.deleteDataSource(999L)).thenReturn(false);

            assertThrows(DataNotFoundException.class, () -> controller.deleteDataSource(999L));
        }
    }

    @Nested
    @DisplayName("POST /api/v1/data-sources/test")
    class TestDataSourceTests {
        @Test
        @DisplayName("测试成功返回结果")
        void shouldReturnTestResult() {
            Map<String, Object> testResult = Map.of("success", true, "response_time", 123);
            Map<String, Object> request = Map.of("type", "ground_station");
            when(dataSourceService.testDataSource(request)).thenReturn(testResult);

            ResponseEntity<Map<String, Object>> response = controller.testDataSource(request);

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(testResult, response.getBody().get("data"));
        }
    }

    @Nested
    @DisplayName("GET /api/v1/data-sources/types")
    class GetDataSourceTypesTests {
        @Test
        @DisplayName("返回类型列表")
        void shouldReturnTypes() {
            List<Map<String, Object>> types = List.of(
                Map.of("value", "ground_station", "label", "地面站")
            );
            when(dataSourceService.getDataSourceTypes()).thenReturn(types);

            ResponseEntity<Map<String, Object>> response = controller.getDataSourceTypes();

            assertEquals(200, response.getStatusCodeValue());
            assertEquals(types, response.getBody().get("data"));
        }
    }
}

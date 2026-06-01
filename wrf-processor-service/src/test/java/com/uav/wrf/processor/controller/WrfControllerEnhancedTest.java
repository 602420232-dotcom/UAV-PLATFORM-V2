package com.uav.wrf.processor.controller;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.quality.Strictness;
import org.mockito.junit.jupiter.MockitoSettings;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import com.uav.wrf.processor.service.WrfDataService;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
@DisplayName("WrfController 增强测试")
@SuppressWarnings("null")
class WrfControllerEnhancedTest {

    private WrfController wrfController;

    @Mock
    private WrfDataService wrfDataService;

    @BeforeEach
    void setUp() {
        wrfController = new WrfController(wrfDataService);
        ReflectionTestUtils.setField(wrfController, "pythonScriptPath", "wrf_processor.py");
        ReflectionTestUtils.setField(wrfController, "dataPath", "./data");
        ReflectionTestUtils.setField(wrfController, "timeout", 30000);

        when(wrfDataService.getWeatherData(anyString())).thenReturn(Map.of("success", true, "data", Map.of()));
        when(wrfDataService.getStatistics(anyString())).thenReturn(Map.of("success", true, "data", Map.of()));
    }

    @Test
    @DisplayName("空文件名返回错误")
    void testEmptyFilename() {
        MockMultipartFile file = new MockMultipartFile("file", "", "application/octet-stream", new byte[0]);
        Map<String, Object> result = wrfController.parseWrfFile(file, 100);
        assertFalse((Boolean) result.get("success"));
        assertEquals("文件名不能为空", result.get("error"));
    }

    @Test
    @DisplayName("null文件名返回错误")
    void testNullFilename() {
        MockMultipartFile file = new MockMultipartFile("file", (String) null, "application/octet-stream", new byte[0]);
        Map<String, Object> result = wrfController.parseWrfFile(file, 100);
        assertFalse((Boolean) result.get("success"));
        assertEquals("文件名不能为空", result.get("error"));
    }

    @Test
    @DisplayName("文件名包含路径遍历返回错误")
    void testPathTraversalInFilename() {
        MockMultipartFile file = new MockMultipartFile("file", "../malicious.nc", "application/octet-stream", new byte[0]);
        Map<String, Object> result = wrfController.parseWrfFile(file, 100);
        assertFalse((Boolean) result.get("success"));
        assertTrue(result.get("error").toString().contains("非法字符"));
    }

    @Test
    @DisplayName("非NetCDF格式返回错误")
    void testNonNetCdfFormat() {
        MockMultipartFile file = new MockMultipartFile("file", "data.txt", "text/plain", "test".getBytes());
        Map<String, Object> result = wrfController.parseWrfFile(file, 100);
        assertFalse((Boolean) result.get("success"));
        assertTrue(result.get("error").toString().contains("仅支持NetCDF"));
    }

    @Test
    @DisplayName("获取气象数据")
    void testGetWeatherData() {
        Map<String, Object> result = wrfController.getWeatherData("test-file-id");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
    }

    @Test
    @DisplayName("获取统计信息")
    void testGetStatistics() {
        Map<String, Object> result = wrfController.getStatistics("test-file-id");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
    }
}

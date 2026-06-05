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

import com.uav.common.script.PythonScriptInvoker;
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

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    @BeforeEach
    void setUp() {
        wrfController = new WrfController(wrfDataService, pythonScriptInvoker);
        ReflectionTestUtils.setField(wrfController, "pythonScriptPath", "wrf_processor.py");
        ReflectionTestUtils.setField(wrfController, "dataPath", "./data");

        when(pythonScriptInvoker.execute(anyString(), anyString(), anyMap()))
            .thenReturn("{\"success\": true}");

        when(wrfDataService.getWeatherData(anyString())).thenReturn(Map.of("success", true, "data", Map.of()));
        when(wrfDataService.getStatistics(anyString())).thenReturn(Map.of("success", true, "data", Map.of()));
        when(wrfDataService.getTurbulence(anyString())).thenReturn(Map.of(
            "success", true, "data",
            Map.of("tke_mean", 1.2, "turbulence_intensity", "MODERATE")
        ));
        when(wrfDataService.getVisibility(anyString())).thenReturn(Map.of(
            "success", true, "data",
            Map.of("visibility_m", 8500.0, "visibility_category", "GOOD")
        ));
        when(wrfDataService.getLightningRisk(anyString())).thenReturn(Map.of(
            "success", true, "data",
            Map.of("risk_level", "LOW", "risk_score", 28.5)
        ));
        when(wrfDataService.getHeightLayers(anyString(), anyList())).thenReturn(Map.of(
            "success", true, "data", Map.of("layers", java.util.List.of(), "layer_count", 0)
        ));
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

    @Test
    @DisplayName("获取湍流数据")
    @SuppressWarnings("unchecked")
    void testGetTurbulence() {
        Map<String, Object> result = wrfController.getTurbulence("test-file-id");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
        assertEquals("MODERATE", ((Map<String, Object>) result.get("data")).get("turbulence_intensity"));
    }

    @Test
    @DisplayName("获取能见度数据")
    @SuppressWarnings("unchecked")
    void testGetVisibility() {
        Map<String, Object> result = wrfController.getVisibility("test-file-id");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
        assertEquals("GOOD", ((Map<String, Object>) result.get("data")).get("visibility_category"));
    }

    @Test
    @DisplayName("获取闪电风险评估")
    @SuppressWarnings("unchecked")
    void testGetLightningRisk() {
        Map<String, Object> result = wrfController.getLightningRisk("test-file-id");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
        assertEquals("LOW", ((Map<String, Object>) result.get("data")).get("risk_level"));
    }

    @Test
    @DisplayName("获取高度分层数据")
    void testGetHeightLayers() {
        Map<String, Object> result = wrfController.getHeightLayers("test-file-id", null);
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
    }

    @Test
    @DisplayName("获取高度分层数据-自定义分层")
    void testGetHeightLayersWithCustomLayers() {
        Map<String, Object> result = wrfController.getHeightLayers("test-file-id", "0,100,500");
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("高级解析-缺少文件路径")
    void testAdvancedParseMissingFilePath() {
        Map<String, Object> result = wrfController.parseWrfAdvanced(Map.of("paramType", "turbulence"));
        assertFalse((Boolean) result.get("success"));
        assertTrue(result.get("error").toString().contains("不能为空"));
    }

    @Test
    @DisplayName("上传WRF数据")
    void testUploadWrfData() {
        when(wrfDataService.createWrfDataFile(anyString(), anyString(), anyLong()))
            .thenReturn(com.uav.wrf.processor.entity.WrfDataFile.builder()
                .fileId("wrf_test").id(1L).build());

        Map<String, Object> result = wrfController.uploadWrfData(Map.of(
            "fileName", "test.nc", "filePath", "./data/test.nc", "fileSize", 1024L
        ));
        assertTrue((Boolean) result.get("success"));
    }
}

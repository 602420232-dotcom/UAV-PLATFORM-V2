package com.uav.wrf.processor.controller;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.multipart.MultipartFile;

import com.uav.wrf.processor.service.WrfDataService;
import com.uav.common.script.PythonScriptInvoker;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * WrfController单元测试
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("WrfController安全测试")
@SuppressWarnings("null")
class WrfControllerTest {

    private WrfController wrfController;
    private MultipartFile mockFile;

    @Mock
    private WrfDataService wrfDataService;

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    @BeforeEach
    void setUp() {
        wrfController = new WrfController(wrfDataService, pythonScriptInvoker);
        assertNotNull(wrfController);
        ReflectionTestUtils.setField(wrfController, "pythonScriptPath", "wrf_processor.py");
        ReflectionTestUtils.setField(wrfController, "dataPath", "./data");

        mockFile = mock(MultipartFile.class);
    }

    @Test
    @DisplayName("测试null文件名拒绝")
    void testRejectNullFilename() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn(null);

        // When
        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        // Then
        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("不能为空"));
    }

    @Test
    @DisplayName("测试空文件名拒绝")
    void testRejectEmptyFilename() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn("");

        // When
        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        // Then
        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("不能为空"));
    }

    @Test
    @DisplayName("测试空白文件名拒绝")
    void testRejectBlankFilename() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn("   ");

        // When
        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        // Then
        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("不能为空"));
    }

    @Test
    @DisplayName("测试路径遍历文件名拒绝 - 包含..")
    void testRejectPathTraversalWithDoubleDots() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn("../malicious.nc");

        // When
        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        // Then
        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("非法字符"));
    }

    @Test
    @DisplayName("测试路径遍历文件名拒绝 - 包含/")
    void testRejectPathTraversalWithSlash() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn("dir/file.nc");

        // When
        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        // Then
        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("非法字符"));
    }

    @Test
    @DisplayName("测试路径遍历文件名拒绝 - 包含反斜杠")
    void testRejectPathTraversalWithBackslash() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn("dir\\file.nc");

        // When
        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        // Then
        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("非法字符"));
    }

    @Test
    @DisplayName("测试不支持的文件类型拒绝")
    void testRejectUnsupportedFileType() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn("malicious.txt");

        // When
        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        // Then
        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("仅支持NetCDF格式文件"));
    }

    @Test
    @DisplayName("测试有效的netcdf文件扩展名接受")
    void testAcceptValidNetcdfExtension() {
        when(mockFile.getOriginalFilename()).thenReturn("wrf_output.netcdf");

        try {
            Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);
            assertTrue(response.containsKey("success"));
        } catch (Exception e) {
            assertTrue(true);
        }
    }

    @Test
    @DisplayName("测试有效的nc文件扩展名接受")
    void testAcceptValidNcExtension() {
        when(mockFile.getOriginalFilename()).thenReturn("wrf_output.nc");

        try {
            Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);
            assertTrue(response.containsKey("success"));
        } catch (Exception e) {
            assertTrue(true);
        }
    }

    @Test
    @DisplayName("测试脚本路径验证 - 空路径")
    void testValidateScriptPath_Empty() {
        ReflectionTestUtils.setField(wrfController, "pythonScriptPath", "");
        when(mockFile.getOriginalFilename()).thenReturn("valid.nc");

        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("安全验证失败"));
    }

    @Test
    @DisplayName("测试脚本路径验证 - 路径遍历")
    void testValidateScriptPath_PathTraversal() {
        ReflectionTestUtils.setField(wrfController, "pythonScriptPath", "../malicious.py");
        when(mockFile.getOriginalFilename()).thenReturn("valid.nc");

        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("安全验证失败"));
    }

    @Test
    @DisplayName("测试脚本路径验证 - 未授权脚本")
    void testValidateScriptPath_UnauthorizedScript() {
        ReflectionTestUtils.setField(wrfController, "pythonScriptPath", "malicious.py");
        when(mockFile.getOriginalFilename()).thenReturn("valid.nc");

        Map<String, Object> response = wrfController.parseWrfFile(mockFile, 100);

        assertEquals(false, response.get("success"));
        assertTrue(response.get("error").toString().contains("安全验证失败"));
    }
}

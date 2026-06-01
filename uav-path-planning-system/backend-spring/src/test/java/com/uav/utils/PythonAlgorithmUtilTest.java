package com.uav.utils;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PythonAlgorithmUtil单元测试
 *
 * <p>测试Python脚本执行器的安全验证功能：
 * <ul>
 *   <li>白名单脚本验证</li>
 *   <li>路径遍历防护</li>
 *   <li>输入验证</li>
 * </ul>
 *
 * @author UAV Team
 * @version 1.0.0
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("PythonAlgorithmUtil安全测试")
class PythonAlgorithmUtilTest {

    private PythonAlgorithmUtil pythonAlgorithmUtil;

    @BeforeEach
    void setUp() {
        pythonAlgorithmUtil = new PythonAlgorithmUtil();
        ReflectionTestUtils.setField(pythonAlgorithmUtil, "scriptPath", "./python");
        ReflectionTestUtils.setField(pythonAlgorithmUtil, "timeout", 30000);
    }

    @Test
    @DisplayName("测试执行白名单脚本 - wrf_parser.py")
    void testExecuteValidScript_WrfParser() {
        // Given
        String scriptName = "wrf/wrf_parser.py";
        Map<String, Object> params = new HashMap<>();
        params.put("input", "test_data");

        // When & Then
        assertDoesNotThrow(() -> {
            String result = pythonAlgorithmUtil.executePythonScript(scriptName, params);
            // 由于测试环境没有Python，实际会返回错误，但不是安全错误
            assertNotNull(result);
        });
    }

    @Test
    @DisplayName("测试执行白名单脚本 - bayesian_assimilation.py")
    void testExecuteValidScript_BayesianAssimilation() {
        // Given
        String scriptName = "assimilation/bayesian_assimilation.py";
        Map<String, Object> params = new HashMap<>();
        params.put("observations", new double[]{1.0, 2.0, 3.0});

        // When & Then
        assertDoesNotThrow(() -> {
            String result = pythonAlgorithmUtil.executePythonScript(scriptName, params);
            assertNotNull(result);
        });
    }

    @Test
    @DisplayName("测试执行白名单脚本 - meteor_forecast.py")
    void testExecuteValidScript_MeteorForecast() {
        // Given
        String scriptName = "prediction/meteor_forecast.py";
        Map<String, Object> params = new HashMap<>();
        params.put("location", "Beijing");
        params.put("hours", 24);

        // When & Then
        assertDoesNotThrow(() -> {
            String result = pythonAlgorithmUtil.executePythonScript(scriptName, params);
            assertNotNull(result);
        });
    }

    @Test
    @DisplayName("测试执行白名单脚本 - three_layer_planner.py")
    void testExecuteValidScript_ThreeLayerPlanner() {
        // Given
        String scriptName = "path-planning/three_layer_planner.py";
        Map<String, Object> params = new HashMap<>();
        params.put("start", new double[]{0, 0, 0});
        params.put("end", new double[]{100, 100, 50});

        // When & Then
        assertDoesNotThrow(() -> {
            String result = pythonAlgorithmUtil.executePythonScript(scriptName, params);
            assertNotNull(result);
        });
    }

    @Test
    @DisplayName("测试拒绝非法脚本名称")
    void testRejectInvalidScriptName() {
        // Given
        String invalidScriptName = "malicious.py";
        Map<String, Object> params = new HashMap<>();

        // When & Then
        Exception exception = assertThrows(SecurityException.class, () -> {
            pythonAlgorithmUtil.executePythonScript(invalidScriptName, params);
        });

        assertTrue(exception.getMessage().contains("未授权的脚本"));
    }

    @Test
    @DisplayName("测试拒绝路径遍历攻击 - ../etc/passwd")
    void testRejectPathTraversal() {
        // Given
        String pathTraversalScript = "../etc/passwd";
        Map<String, Object> params = new HashMap<>();

        // When & Then
        Exception exception = assertThrows(SecurityException.class, () -> {
            pythonAlgorithmUtil.executePythonScript(pathTraversalScript, params);
        });

        assertTrue(exception.getMessage().contains("非法字符") ||
                   exception.getMessage().contains("未授权的脚本"));
    }

    @Test
    @DisplayName("测试拒绝空脚本名称")
    void testRejectEmptyScriptName() {
        // Given
        String emptyScriptName = "";
        Map<String, Object> params = new HashMap<>();

        // When & Then
        Exception exception = assertThrows(SecurityException.class, () -> {
            pythonAlgorithmUtil.executePythonScript(emptyScriptName, params);
        });

        assertTrue(exception.getMessage().contains("不能为空"));
    }

    @Test
    @DisplayName("测试拒绝空白脚本名称")
    void testRejectBlankScriptName() {
        // Given
        String blankScriptName = "   ";
        Map<String, Object> params = new HashMap<>();

        // When & Then
        Exception exception = assertThrows(SecurityException.class, () -> {
            pythonAlgorithmUtil.executePythonScript(blankScriptName, params);
        });

        assertTrue(exception.getMessage().contains("不能为空"));
    }

    @Test
    @DisplayName("测试拒绝包含~的脚本名称")
    void testRejectScriptWithTilde() {
        // Given
        String scriptWithTilde = "~/malicious.py";
        Map<String, Object> params = new HashMap<>();

        // When & Then
        Exception exception = assertThrows(SecurityException.class, () -> {
            pythonAlgorithmUtil.executePythonScript(scriptWithTilde, params);
        });

        assertTrue(exception.getMessage().contains("非法字符"));
    }

    @Test
    @DisplayName("测试脚本名称验证 - 包含双点")
    void testRejectScriptWithDoubleDots() {
        // Given
        String scriptWithDoubleDots = "../malicious.py";
        Map<String, Object> params = new HashMap<>();

        // When & Then
        Exception exception = assertThrows(SecurityException.class, () -> {
            pythonAlgorithmUtil.executePythonScript(scriptWithDoubleDots, params);
        });

        assertTrue(exception.getMessage().contains("非法字符"));
    }

    @Test
    @DisplayName("测试null脚本名称")
    void testRejectNullScriptName() {
        // Given
        String nullScriptName = null;
        Map<String, Object> params = new HashMap<>();

        // When & Then
        Exception exception = assertThrows(SecurityException.class, () -> {
            pythonAlgorithmUtil.executePythonScript(nullScriptName, params);
        });

        assertTrue(exception.getMessage().contains("不能为空"));
    }
}

package com.path.planning.utils;

import com.uav.common.script.PythonScriptInvoker;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationContext;

import java.util.HashMap;
import java.util.Map;

/**
 * Python 脚本执行器
 *
 * @deprecated 请使用 {@link PythonScriptInvoker} 替代。
 * 此类为向后兼容保留，所有调用委托给 common-utils 中的 PythonScriptInvoker。
 */
@Deprecated
public class PythonExecutor {

    private static final Logger log = LoggerFactory.getLogger(PythonExecutor.class);
    private static PythonScriptInvoker delegate;

    /**
     * 初始化委托对象（由 Spring 容器在启动时调用）
     */
    public static void init(ApplicationContext context) {
        delegate = context.getBean(PythonScriptInvoker.class);
        log.info("PythonExecutor initialized with delegate: PythonScriptInvoker");
    }

    public static Map<String, Object> execute(String pythonScript, String action, Map<String, Object> request) {
        if (delegate == null) {
            log.warn("PythonScriptInvoker not initialized, trying fallback execution");
            return fallbackExecute(pythonScript, action, request);
        }
        try {
            String result = delegate.execute(pythonScript, action, request);
            return Map.of("success", true, "data", result);
        } catch (Exception e) {
            log.error("Python 脚本执行失败: {} {}: {}", pythonScript, action, e.getMessage());
            return Map.of("success", false, "error", "处理失败");
        }
    }

    private static Map<String, Object> fallbackExecute(String pythonScript, String action, Map<String, Object> request) {
        // 原始 ProcessBuilder 方式的回退执行
        try {
            com.fasterxml.jackson.databind.ObjectMapper objectMapper = new com.fasterxml.jackson.databind.ObjectMapper();
            java.nio.file.Path tempFile = java.nio.file.Files.createTempFile("python_", ".json");
            try {
                objectMapper.writeValue(tempFile.toFile(), request);
                ProcessBuilder pb = new ProcessBuilder("python3", pythonScript, action, tempFile.toString());
                pb.redirectErrorStream(true);
                Process process = pb.start();

                java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(process.getInputStream()));
                StringBuilder output = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line);
                }
                int exitCode = process.waitFor();
                return Map.of("success", exitCode == 0, "data", output.toString());
            } finally {
                try { java.nio.file.Files.deleteIfExists(tempFile); } catch (Exception ignored) {}
            }
        } catch (Exception e) {
            log.error("Fallback execution failed: {}", e.getMessage());
            return Map.of("success", false, "error", "处理失败");
        }
    }
}

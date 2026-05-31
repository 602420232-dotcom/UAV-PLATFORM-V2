package com.uav.common.feign;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Python脚本统一调用器
 * 
 * 提供安全、高效的Python脚本执行能力，
 * 替代各服务中重复的PythonExecutor实现。
 * 
 * 安全特性：
 * - 脚本白名单验证
 * - 操作白名单验证
 * - 路径遍历防护
 * - 超时控制
 * - 进程资源清理
 * 
 * 使用示例：
 * ```java
 * @Autowired
 * private PythonScriptInvoker scriptInvoker;
 * 
 * Map<String, Object> result = scriptInvoker.execute("meteor_forecast.py", "predict", params);
 * ```
 */
@Slf4j
@Component
public class PythonScriptInvoker {

    // 允许执行的脚本白名单
    private static final Set<String> ALLOWED_SCRIPTS = Set.of(
            "meteor_forecast.py",
            "path_planner.py",
            "assimilation.py",
            "three_layer_planner.py",
            "advanced_planners.py",
            "wrf_processor.py",
            "data_assimilation.py",
            "reinforcement_learning.py",
            "wrf/wrf_parser.py",
            "assimilation/bayesian_assimilation.py",
            "prediction/meteor_forecast.py",
            "path-planning/three_layer_planner.py",
            "vrp/optimize_routes.py"
    );

    // 允许执行的操作白名单
    private static final Set<String> ALLOWED_ACTIONS = Set.of(
            "predict", "plan", "compute", "assimilate", "optimize",
            "vrptw", "astar", "dwa", "full",
            "global_path", "local_avoidance",
            "parse", "validate", "transform",
            "execute", "batch", "variance",
            "correct", "get_forecast", "get_detailed_forecast", "get_realtime_weather"
    );

    private static final int MAX_THREAD_POOL_SIZE = 10;
    private static final int THREAD_KEEP_ALIVE_SECONDS = 60;

    @Value("${uav.python.script-path:src/main/python}")
    private String scriptPath;

    @Value("${uav.python.timeout:30000}")
    private int timeout;

    @Value("${uav.python.enabled:true}")
    private boolean enabled;

    private final ExecutorService executorService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public PythonScriptInvoker() {
        this.executorService = new ThreadPoolExecutor(
                2,
                MAX_THREAD_POOL_SIZE,
                THREAD_KEEP_ALIVE_SECONDS,
                TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(100),
                new ThreadPoolExecutor.CallerRunsPolicy()
        );
    }

    /**
     * 执行Python脚本
     * 
     * @param scriptName 脚本文件名（必须在白名单中）
     * @param action 操作名称（必须在白名单中）
     * @param params 输入参数
     * @return 执行结果
     */
    public String execute(String scriptName, String action, Map<String, Object> params) {
        return execute(scriptName, action, params, timeout);
    }

    /**
     * 执行Python脚本（自定义超时）
     * 
     * @param scriptName 脚本文件名
     * @param action 操作名称
     * @param params 输入参数
     * @param timeoutMs 超时时间（毫秒）
     * @return 执行结果
     */
    public String execute(String scriptName, String action, Map<String, Object> params, int timeoutMs) {
        // 安全验证
        validateScriptName(scriptName);
        validateAction(action);

        if (!enabled) {
            log.warn("Python script execution is disabled");
            return "{\"success\": false, \"error\": \"Python execution disabled\"}";
        }

        log.info("Executing Python script: {} {} (timeout={}ms)", scriptName, action, timeoutMs);

        try {
            // 构建安全的脚本路径
            String scriptFullPath = getSecureScriptPath(scriptName);
            
            // 验证脚本存在
            if (!Files.exists(Paths.get(scriptFullPath))) {
                throw new IllegalArgumentException("Script file does not exist: " + scriptName);
            }

            // 创建临时参数文件
            Path tempFile = Files.createTempFile("python_params_", ".json");
            
            try {
                // 写入参数
                objectMapper.writeValue(tempFile.toFile(), params);

                // 构建命令
                ProcessBuilder pb = new ProcessBuilder(
                        "python3", 
                        scriptFullPath, 
                        action, 
                        tempFile.toString()
                );
                pb.redirectErrorStream(true);

                // 执行并获取结果
                Process process = pb.start();
                
                // 使用Future控制超时
                Future<String> future = executorService.submit(() -> {
                    StringBuilder output = new StringBuilder();
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(process.getInputStream()))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            output.append(line).append("\n");
                        }
                    }
                    return output.toString();
                });

                try {
                    String result = future.get(timeoutMs, TimeUnit.MILLISECONDS);
                    int exitValue = process.waitFor();
                    
                    log.info("Python script completed: {} {} (exit={})", 
                            scriptName, action, exitValue);
                    
                    if (exitValue != 0 && result.isEmpty()) {
                        return "{\"success\": false, \"error\": \"Script execution failed with exit code: " + exitValue + "\"}";
                    }
                    
                    return result;
                    
                } catch (TimeoutException e) {
                    process.destroyForcibly();
                    future.cancel(true);
                    log.error("Python script timeout: {} {}", scriptName, action);
                    return "{\"success\": false, \"error\": \"Execution timeout after " + timeoutMs + "ms\"}";
                }

            } finally {
                // 清理临时文件
                Files.deleteIfExists(tempFile);
            }

        } catch (SecurityException e) {
            log.error("Security validation failed: {}", e.getMessage());
            return "{\"success\": false, \"error\": \"Security validation failed: " + e.getMessage() + "\"}";
        } catch (Exception e) {
            log.error("Python script execution failed: {} {}", scriptName, action, e);
            return "{\"success\": false, \"error\": \"" + e.getMessage() + "\"}";
        }
    }

    /**
     * 异步执行Python脚本
     * 
     * @param scriptName 脚本文件名
     * @param action 操作名称
     * @param params 输入参数
     * @return CompletableFuture结果
     */
    public CompletableFuture<String> executeAsync(String scriptName, String action, Map<String, Object> params) {
        return CompletableFuture.supplyAsync(() -> execute(scriptName, action, params), executorService);
    }

    /**
     * 执行带重试的脚本调用
     * 
     * @param scriptName 脚本文件名
     * @param action 操作名称
     * @param params 输入参数
     * @param maxRetries 最大重试次数
     * @return 执行结果
     */
    public String executeWithRetry(String scriptName, String action, Map<String, Object> params, int maxRetries) {
        int attempts = 0;
        Exception lastException = null;

        while (attempts < maxRetries) {
            try {
                String result = execute(scriptName, action, params);
                if (result != null && !result.contains("\"success\": false")) {
                    return result;
                }
            } catch (Exception e) {
                lastException = e;
            }
            
            attempts++;
            if (attempts < maxRetries) {
                log.warn("Retry {}/{} for script {} {}", attempts, maxRetries, scriptName, action);
                try {
                    Thread.sleep(1000 * attempts); // 指数退避
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }

        log.error("All retries exhausted for script {} {}", scriptName, action, lastException);
        return "{\"success\": false, \"error\": \"All retries exhausted: " + (lastException != null ? lastException.getMessage() : "unknown") + "\"}";
    }

    /**
     * 验证脚本名称
     */
    private void validateScriptName(String scriptName) {
        if (scriptName == null || scriptName.trim().isEmpty()) {
            throw new SecurityException("Script name cannot be null or empty");
        }
        
        // 检查路径遍历（允许子目录，通过getSecureScriptPath的归一化进行防护）
        if (scriptName.contains("..") || scriptName.contains("\\")) {
            throw new SecurityException("Invalid script name: path traversal detected");
        }
        
        // 检查白名单
        if (!ALLOWED_SCRIPTS.contains(scriptName)) {
            throw new SecurityException("Script not in allowed list: " + scriptName);
        }
    }

    /**
     * 验证操作名称
     */
    private void validateAction(String action) {
        if (action == null || action.trim().isEmpty()) {
            throw new SecurityException("Action cannot be null or empty");
        }
        
        if (!ALLOWED_ACTIONS.contains(action)) {
            throw new SecurityException("Action not in allowed list: " + action);
        }
    }

    /**
     * 构建安全的脚本路径
     */
    private String getSecureScriptPath(String scriptName) {
        String basePath = scriptPath.isEmpty() ? "src/main/python" : scriptPath;
        Path fullPath = Paths.get(basePath, scriptName).normalize();
        Path baseDir = Paths.get(basePath).normalize();
        
        // 防止路径遍历攻击
        if (!fullPath.startsWith(baseDir)) {
            throw new SecurityException("Path traversal attempt detected");
        }
        
        return fullPath.toString();
    }

    /**
     * 检查Python环境是否可用
     */
    public boolean isPythonAvailable() {
        try {
            Process process = new ProcessBuilder("python3", "--version")
                    .redirectErrorStream(true)
                    .start();
            int exitCode = process.waitFor();
            return exitCode == 0;
        } catch (Exception e) {
            log.warn("Python is not available", e);
            return false;
        }
    }

    /**
     * 获取允许的脚本列表
     */
    public Set<String> getAllowedScripts() {
        return ALLOWED_SCRIPTS;
    }

    /**
     * 获取允许的操作列表
     */
    public Set<String> getAllowedActions() {
        return ALLOWED_ACTIONS;
    }

    /**
     * 关闭执行器
     */
    public void shutdown() {
        executorService.shutdown();
        try {
            if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
        } catch (InterruptedException e) {
            executorService.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }

    /**
     * 执行Python脚本并返回解析后的Map结果
     */
    public Map<String, Object> executeAsMap(String scriptName, String action, Map<String, Object> params) {
        String result = execute(scriptName, action, params);
        try {
            return objectMapper.readValue(result, new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            log.warn("Failed to parse Python result as Map, returning raw: {}", e.getMessage());
            return Map.of("success", false, "error", "Failed to parse result", "raw", result);
        }
    }
}

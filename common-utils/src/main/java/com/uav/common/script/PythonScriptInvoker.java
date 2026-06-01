package com.uav.common.script;

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

@Slf4j
@Component
public class PythonScriptInvoker {

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
    private final ObjectMapper objectMapper;

    public PythonScriptInvoker(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.executorService = new ThreadPoolExecutor(
                2,
                MAX_THREAD_POOL_SIZE,
                THREAD_KEEP_ALIVE_SECONDS,
                TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(100),
                new ThreadPoolExecutor.CallerRunsPolicy()
        );
    }

    public String execute(String scriptName, String action, Map<String, Object> params) {
        return execute(scriptName, action, params, timeout);
    }

    public String execute(String scriptName, String action, Map<String, Object> params, int timeoutMs) {
        validateScriptName(scriptName);
        validateAction(action);

        if (!enabled) {
            log.warn("Python script execution is disabled");
            return "{\"success\": false, \"error\": \"Python execution disabled\"}";
        }

        log.info("Executing Python script: {} {} (timeout={}ms)", scriptName, action, timeoutMs);

        try {
            String scriptFullPath = getSecureScriptPath(scriptName);

            if (!Files.exists(Paths.get(scriptFullPath))) {
                throw new IllegalArgumentException("Script file does not exist: " + scriptName);
            }

            Path tempFile = Files.createTempFile("python_params_", ".json");

            try {
                objectMapper.writeValue(tempFile.toFile(), params);

                ProcessBuilder pb = new ProcessBuilder(
                        "python3",
                        scriptFullPath,
                        action,
                        tempFile.toString()
                );
                pb.redirectErrorStream(true);

                Process process = pb.start();

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

    public CompletableFuture<String> executeAsync(String scriptName, String action, Map<String, Object> params) {
        return CompletableFuture.supplyAsync(() -> execute(scriptName, action, params), executorService);
    }

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
                    Thread.sleep(1000 * attempts);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }

        log.error("All retries exhausted for script {} {}", scriptName, action, lastException);
        return "{\"success\": false, \"error\": \"All retries exhausted: " + (lastException != null ? lastException.getMessage() : "unknown") + "\"}";
    }

    private void validateScriptName(String scriptName) {
        if (scriptName == null || scriptName.trim().isEmpty()) {
            throw new SecurityException("Script name cannot be null or empty");
        }

        if (scriptName.contains("..") || scriptName.contains("\\")) {
            throw new SecurityException("Invalid script name: path traversal detected");
        }

        if (!ALLOWED_SCRIPTS.contains(scriptName)) {
            throw new SecurityException("Script not in allowed list: " + scriptName);
        }
    }

    private void validateAction(String action) {
        if (action == null || action.trim().isEmpty()) {
            throw new SecurityException("Action cannot be null or empty");
        }

        if (!ALLOWED_ACTIONS.contains(action)) {
            throw new SecurityException("Action not in allowed list: " + action);
        }
    }

    private String getSecureScriptPath(String scriptName) {
        String basePath = scriptPath.isEmpty() ? "src/main/python" : scriptPath;
        Path fullPath = Paths.get(basePath, scriptName).normalize();
        Path baseDir = Paths.get(basePath).normalize();

        if (!fullPath.startsWith(baseDir)) {
            throw new SecurityException("Path traversal attempt detected");
        }

        return fullPath.toString();
    }

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

    public Set<String> getAllowedScripts() {
        return ALLOWED_SCRIPTS;
    }

    public Set<String> getAllowedActions() {
        return ALLOWED_ACTIONS;
    }

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

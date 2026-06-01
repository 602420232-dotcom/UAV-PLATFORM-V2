package com.uav.common.utils;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Set;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@Slf4j
@Component
public class PythonExecutor {

    private static final Set<String> ALLOWED_SCRIPTS = Set.of(
        "meteor_forecast.py",
        "path_planner.py",
        "assimilation.py",
        "three_layer_planner.py",
        "advanced_planners.py"
    );

    private static final Set<String> ALLOWED_ACTIONS = Set.of(
        "predict",
        "plan",
        "compute",
        "assimilate",
        "optimize",
        "vrptw",
        "global_path",
        "local_avoidance"
    );
    
    private static final int MAX_THREAD_POOL_SIZE = 10;
    private static final int THREAD_KEEP_ALIVE_SECONDS = 60;

    @Value("${uav.python.script-path:}")
    private String scriptPath;

    @Value("${uav.python.timeout:30000}")
    private int timeout;

    private final ExecutorService executorService = new ThreadPoolExecutor(
        2,                                              // corePoolSize
        MAX_THREAD_POOL_SIZE,                           // maximumPoolSize
        THREAD_KEEP_ALIVE_SECONDS,                     // keepAliveTime
        TimeUnit.SECONDS,                               // unit
        new LinkedBlockingQueue<>(100),                // queue capacity
        new ThreadPoolExecutor.CallerRunsPolicy()       // rejection policy
    );
    private final ObjectMapper objectMapper = new ObjectMapper();

    public String execute(String scriptName, String action, Map<String, Object> params) {
        validateScriptName(scriptName);
        validateAction(action);

        Path tempFile = null;
        try {
            tempFile = Files.createTempFile("python_exec_", ".json");
            objectMapper.writeValue(tempFile.toFile(), params);

            String scriptFullPath = getSecureScriptPath(scriptName);
            if (!Files.exists(Paths.get(scriptFullPath))) {
                throw new SecurityException("Script file does not exist: " + scriptName);
            }

            ProcessBuilder pb = new ProcessBuilder("python3", scriptFullPath, action, tempFile.toString());
            pb.redirectErrorStream(true);
            Process process = pb.start();

            Future<String> future = executorService.submit(() -> {
                StringBuilder out = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) out.append(line).append("\n");
                }
                return out.toString();
            });

            String result = future.get(timeout, TimeUnit.MILLISECONDS);
            process.waitFor();
            log.info("Python执行完成: {} {} (exit={})", scriptName, action, process.exitValue());
            return result;

        } catch (TimeoutException e) {
            log.error("Python执行超时: {}", scriptName);
            return "{\"error\": \"执行超时\"}";
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Python执行被中断: {}", scriptName, e);
            return "{\"error\": \"执行被中断\"}";
        } catch (ExecutionException e) {
            log.error("Python执行任务错误: {}", scriptName, e);
            return "{\"error\": \"执行任务错误\"}";
        } catch (IOException e) {
            log.error("Python执行IO错误: {}", scriptName, e);
            return "{\"error\": \"IO错误\"}";
        } catch (Exception e) {
            log.error("Python执行错误: {}", scriptName, e);
            return "{\"error\": \"执行错误\"}";
        } finally {
            if (tempFile != null) try { Files.deleteIfExists(tempFile); } catch (IOException ignored) {}
        }
    }

    private void validateScriptName(String scriptName) {
        if (scriptName == null || scriptName.trim().isEmpty()) {
            throw new SecurityException("Script name cannot be null or empty");
        }
        if (scriptName.contains("..") || scriptName.contains("/") || scriptName.contains("\\")) {
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
        
        if (!fullPath.startsWith(Paths.get(basePath).normalize())) {
            throw new SecurityException("Path traversal attempt detected");
        }
        
        return fullPath.toString();
    }

    public void shutdown() {
        executorService.shutdown();
        try { if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) executorService.shutdownNow(); }
        catch (InterruptedException e) { executorService.shutdownNow(); Thread.currentThread().interrupt(); }
    }
}

package com.uav.common.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.exception.PythonExecutionException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@Slf4j
@Component
public class PythonScriptInvoker {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final ExecutorService executorService = new ThreadPoolExecutor(
        2, 10, 60L, TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(100),
        new ThreadPoolExecutor.CallerRunsPolicy()
    );

    @Value("${uav.python.timeout:30000}")
    private int timeout;

    public Map<String, Object> execute(String pythonScriptPath, String action, Map<String, Object> request) {
        validateScriptPath(pythonScriptPath);

        Path tempFile = null;
        Process process = null;
        try {
            tempFile = Files.createTempFile("py_invoke_", ".json");
            objectMapper.writeValue(tempFile.toFile(), request);

            ProcessBuilder pb = new ProcessBuilder("python3", pythonScriptPath, action, tempFile.toString());
            pb.redirectErrorStream(true);
            final Process runningProcess = pb.start();
            process = runningProcess;

            Future<String> future = executorService.submit(() -> {
                StringBuilder out = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(runningProcess.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        out.append(line);
                    }
                }
                return out.toString();
            });

            String output = future.get(timeout, TimeUnit.MILLISECONDS);
            int exitCode = process.waitFor();

            log.debug("Python执行完成: {} {} (exit={})", pythonScriptPath, action, exitCode);

            return Map.of("success", exitCode == 0, "data", exitCode == 0 ? output : "Python脚本执行失败");

        } catch (TimeoutException e) {
            log.error("Python脚本执行超时: {} {}", pythonScriptPath, action);
            return Map.of("success", false, "error", "算法执行超时");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Python脚本执行被中断: {} {}", pythonScriptPath, action);
            throw new PythonExecutionException(pythonScriptPath, "Python执行被中断", e);
        } catch (IOException e) {
            log.error("Python脚本执行IO错误: {} {} - {}", pythonScriptPath, action, e.getMessage());
            throw new PythonExecutionException(pythonScriptPath, "Python执行IO错误", e);
        } catch (ExecutionException e) {
            log.error("Python脚本执行错误: {} {} - {}", pythonScriptPath, action, e.getMessage());
            throw new PythonExecutionException(pythonScriptPath, "Python执行任务错误", e);
        } catch (Exception e) {
            log.error("Python脚本执行失败: {} {} - {}", pythonScriptPath, action, e.getMessage());
            throw new PythonExecutionException(pythonScriptPath, "Python执行错误", e);
        } finally {
            if (process != null) process.destroy();
            if (tempFile != null) {
                try { Files.deleteIfExists(tempFile); } catch (IOException ignored) {}
            }
        }
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

    private void validateScriptPath(String pythonScriptPath) {
        if (pythonScriptPath == null || pythonScriptPath.isEmpty()) {
            throw new PythonExecutionException("", "Script path cannot be empty", null);
        }
        Path path = Paths.get(pythonScriptPath).normalize().toAbsolutePath();
        if (pythonScriptPath.contains("..") || !Files.exists(path)) {
            throw new PythonExecutionException(pythonScriptPath, "Invalid or non-existent script path", null);
        }
    }
}

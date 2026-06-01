package com.wrf.processor.controller;
import org.springframework.web.bind.annotation.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.multipart.MultipartFile;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
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

@RestController
@RequestMapping("/api/wrf")
@Slf4j
public class WrfController {

    private static final Set<String> ALLOWED_SCRIPT_NAMES = Set.of(
        "wrf_processor.py",
        "wrf_parser.py",
        "wrf_converter.py"
    );

    @Value("${wrf.python-script:wrf_processor.py}")
    private String pythonScriptPath;

    @Value("${wrf.data-path:./data}")
    private String dataPath;

    @Value("${wrf.timeout:30000}")
    private int timeout;

    private final ExecutorService executorService = new ThreadPoolExecutor(
        2, 10, 60L, TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(100),
        new ThreadPoolExecutor.CallerRunsPolicy()
    );

    @PostMapping("/parse")
    public Map<String, Object> parseWrfFile(@RequestParam("file") MultipartFile file,
                                            @RequestParam(value = "height", defaultValue = "100") int height) {
        Path tempFile = null;
        try {
            String originalName = file.getOriginalFilename();
            if (originalName == null || originalName.isBlank()) {
                return Map.of("success", false, "error", "文件名不能为空");
            }
            if (originalName.contains("..") || originalName.contains("/") || originalName.contains("\\")) {
                return Map.of("success", false, "error", "文件名包含非法字符");
            }
            if (!originalName.endsWith(".nc") && !originalName.endsWith(".netcdf")) {
                return Map.of("success", false, "error", "仅支持NetCDF格式文件");
            }

            validateScriptPath(pythonScriptPath);

            String safeName = UUID.randomUUID().toString() + "_" + originalName.replaceAll("[^a-zA-Z0-9._-]", "_");
            tempFile = Paths.get(dataPath, safeName).normalize();

            if (!tempFile.startsWith(Paths.get(dataPath).normalize())) {
                return Map.of("success", false, "error", "路径遍历攻击检测");
            }

            Files.createDirectories(tempFile.getParent());
            file.transferTo(tempFile.toFile());

            ProcessBuilder processBuilder = new ProcessBuilder(
                "python3", pythonScriptPath, tempFile.toString(), String.valueOf(height)
            );
            processBuilder.redirectErrorStream(true);

            Future<String> future = executorService.submit(() -> {
                StringBuilder output = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(processBuilder.start().getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        output.append(line).append("\n");
                    }
                }
                return output.toString();
            });

            String result = future.get(timeout, TimeUnit.MILLISECONDS);

            return Map.of(
                "success", true,
                "data", result
            );

        } catch (TimeoutException e) {
            log.error("WRF处理超时: {}", e.getMessage());
            return Map.of("success", false, "error", "处理超时");
        } catch (SecurityException e) {
            log.error("安全异常: {}", e.getMessage());
            return Map.of("success", false, "error", "安全验证失败: " + e.getMessage());
        } catch (IOException e) {
            log.error("IO错误: {}", e.getMessage());
            return Map.of("success", false, "error", "文件处理错误");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("处理被中断: {}", e.getMessage());
            return Map.of("success", false, "error", "处理被中断");
        } catch (ExecutionException e) {
            log.error("执行错误: {}", e.getMessage());
            return Map.of("success", false, "error", "执行错误");
        } catch (Exception e) {
            log.error("处理失败: {}", e.getMessage(), e);
            return Map.of("success", false, "error", "处理失败: " + e.getClass().getSimpleName());
        } finally {
            if (tempFile != null) {
                try {
                    Files.deleteIfExists(tempFile);
                } catch (IOException ignored) {
                }
            }
        }
    }

    private void validateScriptPath(String scriptPath) {
        if (scriptPath == null || scriptPath.isBlank()) {
            throw new SecurityException("脚本路径不能为空");
        }
        if (scriptPath.contains("..") || scriptPath.contains("~")) {
            throw new SecurityException("脚本路径包含非法字符");
        }
        String scriptName = Paths.get(scriptPath).getFileName().toString();
        if (!ALLOWED_SCRIPT_NAMES.contains(scriptName)) {
            throw new SecurityException("未授权的脚本: " + scriptName);
        }
    }

    @GetMapping("/data")
    public Map<String, Object> getWeatherData(@RequestParam("fileId") String fileId) {
        return Map.of(
            "success", true,
            "data", Map.of()
        );
    }

    @GetMapping("/stats")
    public Map<String, Object> getStatistics(@RequestParam("fileId") String fileId) {
        return Map.of(
            "success", true,
            "data", Map.of()
        );
    }
}

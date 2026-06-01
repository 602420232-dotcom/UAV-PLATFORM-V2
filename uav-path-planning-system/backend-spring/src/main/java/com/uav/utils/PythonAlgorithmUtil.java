package com.uav.utils;
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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.LinkedBlockingQueue;

/**
 * Python算法执行工具类
 *
 * <p>提供安全的Python脚本执行接口，支持以下功能：
 * <ul>
 *   <li>白名单验证 - 仅允许执行预定义的脚本</li>
 *   <li>路径遍历防护 - 防止路径遍历攻击</li>
 *   <li>超时控制 - 防止脚本无限期执行</li>
 *   <li>异步执行 - 使用线程池异步执行脚本</li>
 * </ul>
 *
 * <p>使用示例：
 * <pre>
 * {@code
 * @Autowired
 * private PythonAlgorithmUtil pythonUtil;
 *
 * Map<String, Object> params = Map.of("input", data);
 * String result = pythonUtil.executePythonScript("wrf/wrf_parser.py", params);
 * }
 * </pre>
 *
 * @author UAV Team
 * @version 1.0.0
 */
@Slf4j
@Component
public class PythonAlgorithmUtil {

    private static final Set<String> ALLOWED_SCRIPTS = Set.of(
        "wrf/wrf_parser.py",
        "assimilation/bayesian_assimilation.py",
        "prediction/meteor_forecast.py",
        "path-planning/three_layer_planner.py",
        "vrp/optimize_routes.py"
    );

    @Value("${uav.python.script-path:./python}")
    private String scriptPath;

    @Value("${uav.python.timeout:30000}")
    private int timeout;

    private final ExecutorService executorService = new ThreadPoolExecutor(
        2, 10, 60L, TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(100),
        new ThreadPoolExecutor.CallerRunsPolicy()
    );
    private final ObjectMapper objectMapper = new ObjectMapper();

    public String executePythonScript(String scriptName, Map<String, Object> params) {
        Path tempFile = null;
        try {
            validateScriptName(scriptName);

            tempFile = Files.createTempFile("python_algo_", ".json");
            objectMapper.writeValue(tempFile.toFile(), params);

            String scriptFullPath = getSecureScriptPath(scriptName);
            ProcessBuilder processBuilder = new ProcessBuilder(
                "python3", scriptFullPath, tempFile.toString()
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
            log.info("Python脚本执行完成: {}", scriptName);
            return result;

        } catch (TimeoutException e) {
            log.error("Python脚本执行超时: {}", scriptName, e);
            return "{\"error\": \"执行超时\"}";
        } catch (SecurityException e) {
            log.error("安全验证失败: {}", scriptName, e);
            return "{\"error\": \"安全验证失败: \" + e.getMessage() + \"\"}";
        } catch (IOException e) {
            log.error("IO错误: {}", scriptName, e);
            return "{\"error\": \"文件IO错误\"}";
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("执行被中断: {}", scriptName, e);
            return "{\"error\": \"执行被中断\"}";
        } catch (ExecutionException e) {
            log.error("执行错误: {}", scriptName, e);
            return "{\"error\": \"执行错误\"}";
        } catch (Exception e) {
            log.error("执行Python脚本时发生错误: {}", scriptName, e);
            return "{\"error\": \"执行错误: \" + e.getClass().getSimpleName() + \"\"}";
        } finally {
            if (tempFile != null) {
                try {
                    Files.deleteIfExists(tempFile);
                } catch (IOException ignored) {
                }
            }
        }
    }

    private void validateScriptName(String scriptName) {
        if (scriptName == null || scriptName.isBlank()) {
            throw new SecurityException("脚本名称不能为空");
        }
        if (scriptName.contains("..") || scriptName.contains("~")) {
            throw new SecurityException("脚本名称包含非法字符");
        }
        if (!ALLOWED_SCRIPTS.contains(scriptName)) {
            throw new SecurityException("未授权的脚本: " + scriptName);
        }
    }

    private String getSecureScriptPath(String scriptName) {
        Path fullPath = Paths.get(scriptPath, scriptName).normalize();
        Path basePath = Paths.get(scriptPath).normalize();

        if (!fullPath.startsWith(basePath)) {
            throw new SecurityException("路径遍历攻击检测");
        }

        return fullPath.toString();
    }

    public String parseWRFData(String filePath, int height) {
        Map<String, Object> params = Map.of("file_path", filePath, "height", height);
        return executePythonScript("wrf/wrf_parser.py", params);
    }

    public String performBayesianAssimilation(String backgroundData, String observationData) {
        Map<String, Object> params = Map.of("background", backgroundData, "observations", observationData);
        return executePythonScript("assimilation/bayesian_assimilation.py", params);
    }

    public String correctMeteorData(String wrfData, String historicalData) {
        Map<String, Object> params = Map.of("wrf_data", wrfData, "historical_data", historicalData);
        return executePythonScript("prediction/meteor_forecast.py", params);
    }

    public String planPath(String tasks, String drones, String weatherData) {
        Map<String, Object> params = Map.of("tasks", tasks, "drones", drones, "weather_data", weatherData);
        return executePythonScript("path-planning/three_layer_planner.py", params);
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
}

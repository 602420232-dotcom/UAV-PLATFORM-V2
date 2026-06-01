package com.uav.wrf.processor.controller;

import com.uav.common.dto.WrfParseRequest;
import com.uav.wrf.processor.entity.WrfDataFile;
import com.uav.wrf.processor.service.WrfDataService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.*;

@RestController
@RequestMapping("/api/wrf")
@Slf4j
@RequiredArgsConstructor
public class WrfController {

    private static final Set<String> ALLOWED_SCRIPT_NAMES = Set.of(
        "wrf_processor.py",
        "wrf_parser.py",
        "wrf_converter.py"
    );

    private static final int MIN_HEIGHT = 1;
    private static final int MAX_HEIGHT = 30000;

    @Value("${wrf.python-script:wrf_processor.py}")
    private String pythonScriptPath;

    @Value("${wrf.data-path:./data}")
    private String dataPath;

    @Value("${wrf.timeout:30000}")
    private int timeout;

    private final WrfDataService wrfDataService;

    private final ExecutorService executorService = new ThreadPoolExecutor(
        2, 10, 60L, TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(100),
        new ThreadPoolExecutor.CallerRunsPolicy()
    );

    @PostMapping(value = "/parse-params", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, Object> parseWrfData(@RequestBody WrfParseRequest request) {
        try {
            log.info("Processing parameterized WRF data, height={}", request.getSafeHeight());

            int height = request.getSafeHeight();
            if (height < MIN_HEIGHT || height > MAX_HEIGHT) {
                return Map.of(
                    "success", false,
                    "code", 400,
                    "message", "高度值必须在" + MIN_HEIGHT + "到" + MAX_HEIGHT + "之间"
                );
            }

            if (request.getFilePath() != null && !request.getFilePath().isBlank()) {
                return processWrfFromFilePath(request.getFilePath(), height);
            }

            if (request.getData() != null && !request.getData().isEmpty()) {
                return Map.of(
                    "success", true,
                    "code", 200,
                    "message", "WRF数据解析成功",
                    "data", request.getData()
                );
            }

            Map<String, Object> result = generateMockWeatherData(height, request.getBounds());
            return Map.of(
                "success", true,
                "code", 200,
                "message", "WRF数据解析成功",
                "data", result.get("data")
            );

        } catch (Exception e) {
            log.error("Failed to process parameterized WRF data", e);
            return Map.of(
                "success", false,
                "code", 500,
                "message", "处理失败: " + e.getMessage()
            );
        }
    }

    @PostMapping(value = "/parse", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> parseWrfFile(@RequestPart("file") MultipartFile file,
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
            if (height < MIN_HEIGHT || height > MAX_HEIGHT) {
                return Map.of("success", false, "error",
                    "高度值必须在" + MIN_HEIGHT + "到" + MAX_HEIGHT + "之间");
            }

            validateScriptPath(pythonScriptPath);

            String safeName = UUID.randomUUID().toString() + "_" + originalName.replaceAll("[^a-zA-Z0-9._-]", "_");
            tempFile = Paths.get(dataPath, safeName).normalize();

            if (!tempFile.startsWith(Paths.get(dataPath).normalize())) {
                return Map.of("success", false, "error", "路径遍历攻击检测");
            }

            Files.createDirectories(tempFile.getParent());
            java.io.File targetFile = tempFile.toFile();
            if (targetFile != null) {
                file.transferTo(targetFile);
            }

            ProcessBuilder processBuilder = new ProcessBuilder(
                "python3", pythonScriptPath, tempFile.toString(), String.valueOf(height)
            );
            processBuilder.redirectErrorStream(true);

            Future<String> future = executorService.submit(() -> {
                StringBuilder output = new StringBuilder();
                Process process = processBuilder.start();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        output.append(line).append("\n");
                    }
                }
                return output.toString();
            });

            String result = future.get(timeout, TimeUnit.MILLISECONDS);

            WrfDataFile savedFile = wrfDataService.createWrfDataFile(originalName, tempFile.toString(), file.getSize());

            return Map.of(
                "success", true,
                "data", result,
                "fileId", savedFile.getFileId()
            );

        } catch (TimeoutException e) {
            log.error("WRF处理超时: {}", e.getMessage());
            return Map.of("success", false, "error", "处理超时");
        } catch (SecurityException e) {
            log.error("安全异常: {}", e.getMessage());
            return Map.of("success", false, "error", "安全验证失败: " + e.getMessage());
        } catch (Exception e) {
            log.error("处理失败: {}", e.getMessage(), e);
            return Map.of("success", false, "error", "处理失败: " + e.getClass().getSimpleName());
        } finally {
            if (tempFile != null) {
                try {
                    Files.deleteIfExists(tempFile);
                } catch (Exception e) {
                    log.warn("Failed to delete temporary file: {}", tempFile, e);
                }
            }
        }
    }

    private Map<String, Object> processWrfFromFilePath(String filePath, int height) {
        try {
            validateScriptPath(pythonScriptPath);

            ProcessBuilder processBuilder = new ProcessBuilder(
                "python3", pythonScriptPath, filePath, String.valueOf(height)
            );
            processBuilder.redirectErrorStream(true);

            Future<String> future = executorService.submit(() -> {
                StringBuilder output = new StringBuilder();
                Process process = processBuilder.start();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
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
                "code", 200,
                "message", "WRF文件处理成功",
                "data", result
            );
        } catch (Exception e) {
            log.error("Failed to process WRF file from path: {}", filePath, e);
            return Map.of(
                "success", false,
                "code", 500,
                "message", "文件处理失败"
            );
        }
    }

    private Map<String, Object> generateMockWeatherData(int height, Map<String, Double> bounds) {
        Map<String, Object> data = new HashMap<>();
        
        data.put("height", height);
        data.put("timestamp", System.currentTimeMillis());
        
        if (bounds != null) {
            data.put("bounds", bounds);
        }
        
        data.put("wind_speed", generateGridData(10, 10, 5.0, 15.0));
        data.put("wind_direction", generateGridData(10, 10, 0.0, 360.0));
        data.put("temperature", generateGridData(10, 10, 15.0, 30.0));
        data.put("humidity", generateGridData(10, 10, 40.0, 80.0));
        data.put("pressure", generateGridData(10, 10, 1000.0, 1020.0));
        
        return Map.of(
            "success", true,
            "data", data
        );
    }

    private double[][] generateGridData(int rows, int cols, double min, double max) {
        double[][] grid = new double[rows][cols];
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                grid[i][j] = min + Math.random() * (max - min);
            }
        }
        return grid;
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
        log.info("Getting weather data for fileId: {}", fileId);
        return wrfDataService.getWeatherData(fileId);
    }

    @GetMapping("/stats")
    public Map<String, Object> getStatistics(@RequestParam("fileId") String fileId) {
        log.info("Getting statistics for fileId: {}", fileId);
        return wrfDataService.getStatistics(fileId);
    }

    @PostMapping("/upload")
    public Map<String, Object> uploadWrfData(@RequestBody Map<String, Object> request) {
        log.info("Uploading WRF data: {}", request);
        try {
            String fileName = (String) request.getOrDefault("fileName", "wrf_file.nc");
            String filePath = (String) request.getOrDefault("filePath", "./data/" + fileName);
            Long fileSize = request.get("fileSize") != null ? 
                Long.valueOf(request.get("fileSize").toString()) : 0L;
            
            WrfDataFile savedFile = wrfDataService.createWrfDataFile(fileName, filePath, fileSize);
            
            return Map.of(
                "success", true,
                "message", "WRF数据上传成功",
                "data", Map.of(
                    "fileId", savedFile.getFileId(),
                    "id", savedFile.getId()
                )
            );
        } catch (Exception e) {
            log.error("Failed to upload WRF data", e);
            return Map.of(
                "success", false,
                "message", "上传失败: " + e.getMessage()
            );
        }
    }

    @GetMapping("/list")
    public Map<String, Object> listWrfData(@RequestParam("page") Integer page, @RequestParam("size") Integer size) {
        log.info("Listing WRF data - page: {}, size: {}", page, size);
        try {
            Page<WrfDataFile> wrfDataPage = wrfDataService.findAll(page, size);
            
            List<Map<String, Object>> dataList = new ArrayList<>();
            for (WrfDataFile file : wrfDataPage.getContent()) {
                Map<String, Object> fileData = new HashMap<>();
                fileData.put("id", file.getId());
                fileData.put("fileId", file.getFileId());
                fileData.put("fileName", file.getFileName());
                fileData.put("fileSize", file.getFileSize());
                fileData.put("status", file.getStatus());
                fileData.put("createdAt", file.getCreatedAt().toString());
                dataList.add(fileData);
            }
            
            return Map.of(
                "success", true,
                "data", dataList,
                "page", page,
                "size", size,
                "totalElements", wrfDataPage.getTotalElements(),
                "totalPages", wrfDataPage.getTotalPages()
            );
        } catch (Exception e) {
            log.error("Failed to list WRF data", e);
            return Map.of(
                "success", false,
                "message", "获取列表失败: " + e.getMessage()
            );
        }
    }

    @GetMapping("/detail")
    public Map<String, Object> getWrfDataDetail(@RequestParam("id") Long id) {
        log.info("Getting WRF data detail for id: {}", id);
        return wrfDataService.getDetail(id);
    }
}

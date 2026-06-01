package com.uav.wrf.processor.service;

import com.uav.wrf.processor.entity.WrfDataFile;
import com.uav.wrf.processor.repository.WrfDataFileRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class WrfDataService {

    private final WrfDataFileRepository wrfDataFileRepository;

    public Optional<WrfDataFile> findByFileId(String fileId) {
        return wrfDataFileRepository.findByFileId(fileId);
    }

    public Optional<WrfDataFile> findById(Long id) {
        return wrfDataFileRepository.findById(Objects.requireNonNull(id));
    }

    public Page<WrfDataFile> findAll(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return wrfDataFileRepository.findAllByOrderByCreatedAtDesc(pageable);
    }

    public WrfDataFile createWrfDataFile(String fileName, String filePath, Long fileSize) {
        String fileId = "wrf_" + UUID.randomUUID().toString().substring(0, 8);
        
        WrfDataFile wrfDataFile = WrfDataFile.builder()
                .fileId(fileId)
                .fileName(fileName)
                .filePath(filePath)
                .fileSize(fileSize)
                .status("UPLOADED")
                .height(100)
                .timeSteps(24)
                .variables("temperature,humidity,wind_speed,wind_direction,pressure")
                .build();
        
        return wrfDataFileRepository.save(Objects.requireNonNull(wrfDataFile));
    }

    public WrfDataFile updateWrfDataFile(WrfDataFile wrfDataFile) {
        return wrfDataFileRepository.save(Objects.requireNonNull(wrfDataFile));
    }

    public Map<String, Object> getWeatherData(String fileId) {
        Optional<WrfDataFile> optionalWrfDataFile = findByFileId(fileId);
        if (optionalWrfDataFile.isEmpty()) {
            return Map.of(
                "success", false,
                "message", "File not found: " + fileId
            );
        }

        WrfDataFile wrfDataFile = optionalWrfDataFile.get();
        
        Map<String, Object> weatherData = new HashMap<>();
        weatherData.put("fileId", fileId);
        weatherData.put("height", wrfDataFile.getHeight());
        weatherData.put("timeSteps", wrfDataFile.getTimeSteps());
        weatherData.put("variables", wrfDataFile.getVariables() != null 
            ? Arrays.asList(wrfDataFile.getVariables().split(",")) 
            : List.of());
        
        weatherData.put("wind_speed", generateGridData(10, 10, 5.0, 15.0));
        weatherData.put("wind_direction", generateGridData(10, 10, 0.0, 360.0));
        weatherData.put("temperature", generateGridData(10, 10, 15.0, 30.0));
        weatherData.put("humidity", generateGridData(10, 10, 40.0, 80.0));
        weatherData.put("pressure", generateGridData(10, 10, 1000.0, 1020.0));

        return Map.of(
            "success", true,
            "data", weatherData
        );
    }

    public Map<String, Object> getStatistics(String fileId) {
        Optional<WrfDataFile> optionalWrfDataFile = findByFileId(fileId);
        if (optionalWrfDataFile.isEmpty()) {
            return Map.of(
                "success", false,
                "message", "File not found: " + fileId
            );
        }

        Map<String, Object> statistics = new HashMap<>();
        statistics.put("fileId", fileId);
        
        Map<String, Object> windSpeedStats = Map.of(
            "min", 5.2,
            "max", 14.8,
            "mean", 9.5,
            "std", 2.3
        );
        
        Map<String, Object> temperatureStats = Map.of(
            "min", 15.1,
            "max", 29.8,
            "mean", 22.3,
            "std", 3.1
        );
        
        Map<String, Object> humidityStats = Map.of(
            "min", 41.2,
            "max", 79.5,
            "mean", 60.8,
            "std", 8.2
        );
        
        statistics.put("wind_speed", windSpeedStats);
        statistics.put("temperature", temperatureStats);
        statistics.put("humidity", humidityStats);

        return Map.of(
            "success", true,
            "data", statistics
        );
    }

    public Map<String, Object> getDetail(Long id) {
        Optional<WrfDataFile> optionalWrfDataFile = findById(id);
        if (optionalWrfDataFile.isEmpty()) {
            return Map.of(
                "success", false,
                "message", "Record not found with id: " + id
            );
        }

        WrfDataFile wrfDataFile = optionalWrfDataFile.get();
        Map<String, Object> detail = new HashMap<>();
        detail.put("id", wrfDataFile.getId());
        detail.put("fileId", wrfDataFile.getFileId());
        detail.put("fileName", wrfDataFile.getFileName());
        detail.put("fileSize", wrfDataFile.getFileSize());
        detail.put("height", wrfDataFile.getHeight());
        detail.put("timeSteps", wrfDataFile.getTimeSteps());
        detail.put("variables", wrfDataFile.getVariables() != null 
            ? Arrays.asList(wrfDataFile.getVariables().split(",")) 
            : List.of());
        detail.put("status", wrfDataFile.getStatus());
        detail.put("createdAt", wrfDataFile.getCreatedAt() != null ? wrfDataFile.getCreatedAt().toString() : null);
        detail.put("updatedAt", wrfDataFile.getUpdatedAt() != null ? wrfDataFile.getUpdatedAt().toString() : null);

        return Map.of(
            "success", true,
            "data", detail
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
}

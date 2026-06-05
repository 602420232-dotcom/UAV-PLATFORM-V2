package com.uav.radiosonde.weather.controller;

import com.uav.radiosonde.weather.model.RadiosondeData;
import com.uav.radiosonde.weather.repository.RadiosondeDataRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 探空气球数据 Controller
 * 端点路径与 RadiosondeWeatherClient Feign 接口保持一致
 */
@Slf4j
@RestController
@RequestMapping("/api/radiosonde")
@RequiredArgsConstructor
@Tag(name = "探空气球", description = "探空气球数据查询与管理接口")
public class RadiosondeController {

    private final RadiosondeDataRepository repository;

    /**
     * GET /api/radiosonde/data?stationId=50527&level=500
     * 获取探空数据（按站号和可选气压层过滤）
     */
    @GetMapping("/data")
    @Operation(summary = "获取探空数据")
    public ResponseEntity<Map<String, Object>> getSoundingData(
            @RequestParam(value = "stationId") String stationId,
            @RequestParam(value = "level", required = false) Integer level) {
        Map<String, Object> result = new LinkedHashMap<>();
        if (level != null) {
            Page<RadiosondeData> page = repository.findByStationIdAndLevel(
                    stationId, level, PageRequest.of(0, 100));
            result.put("success", true);
            result.put("data", page.getContent());
            result.put("total", page.getTotalElements());
        } else {
            List<RadiosondeData> profile = repository.findLatestProfileByStationId(stationId);
            if (profile.isEmpty()) {
                result.put("success", false);
                result.put("message", "探空数据不存在: stationId=" + stationId);
            } else {
                result.put("success", true);
                result.put("data", profile);
                result.put("stationId", stationId);
                result.put("launchTime", profile.get(0).getLaunchTime());
            }
        }
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/radiosonde/list?page=1&size=10
     * 获取探空站列表
     */
    @GetMapping("/list")
    @Operation(summary = "获取探空站列表")
    public ResponseEntity<Map<String, Object>> listStations(
            @RequestParam(value = "page", defaultValue = "1") Integer page,
            @RequestParam(value = "size", defaultValue = "10") Integer size) {
        List<Object[]> stations = repository.findDistinctStations();
        List<Map<String, Object>> stationList = stations.stream()
                .map(row -> {
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("stationId", row[0]);
                    m.put("stationName", row[1]);
                    m.put("longitude", row[2]);
                    m.put("latitude", row[3]);
                    m.put("stationAltitude", row[4]);
                    return m;
                })
                .collect(Collectors.toList());

        int total = stationList.size();
        int fromIndex = (page - 1) * size;
        int toIndex = Math.min(fromIndex + size, total);
        List<Map<String, Object>> paged = (fromIndex < total)
                ? stationList.subList(fromIndex, toIndex)
                : Collections.emptyList();

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success", true);
        result.put("data", paged);
        result.put("total", total);
        result.put("page", page);
        result.put("size", size);
        result.put("totalPages", (int) Math.ceil((double) total / size));
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/radiosonde/{id}
     * 获取探空数据详情
     */
    @GetMapping("/{id}")
    @Operation(summary = "获取探空数据详情")
    public ResponseEntity<Map<String, Object>> getSoundingDetail(@PathVariable("id") Long id) {
        Map<String, Object> result = new LinkedHashMap<>();
        repository.findById(Objects.requireNonNull(id, "id must not be null")).ifPresentOrElse(
                data -> {
                    result.put("success", true);
                    result.put("data", data);
                },
                () -> {
                    result.put("success", false);
                    result.put("message", "探空数据不存在: id=" + id);
                }
        );
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/radiosonde/skew-t/{id}
     * 获取斜温图数据（该次探空的完整垂直廓线）
     */
    @GetMapping("/skew-t/{id}")
    @Operation(summary = "获取斜温图数据")
    public ResponseEntity<Map<String, Object>> getSkewTData(@PathVariable("id") Long id) {
        Map<String, Object> result = new LinkedHashMap<>();
        repository.findById(Objects.requireNonNull(id, "id must not be null")).ifPresentOrElse(
                data -> {
                    List<RadiosondeData> profile = repository.findLatestProfileByStationId(data.getStationId());

                    List<Double> pressure = new ArrayList<>();
                    List<Double> height = new ArrayList<>();
                    List<Double> temperature = new ArrayList<>();
                    List<Double> dewPoint = new ArrayList<>();
                    List<Double> windSpeed = new ArrayList<>();
                    List<Double> windDirection = new ArrayList<>();

                    for (RadiosondeData r : profile) {
                        pressure.add(r.getPressureLevel().doubleValue());
                        height.add(r.getGeopotentialHeight());
                        temperature.add(r.getTemperature());
                        dewPoint.add(r.getDewPoint());
                        windSpeed.add(r.getWindSpeed());
                        windDirection.add(r.getWindDirection());
                    }

                    result.put("success", true);
                    result.put("stationId", data.getStationId());
                    result.put("stationName", data.getStationName());
                    result.put("launchTime", data.getLaunchTime());
                    result.put("pressure", pressure);
                    result.put("height", height);
                    result.put("temperature", temperature);
                    result.put("dewPoint", dewPoint);
                    result.put("windSpeed", windSpeed);
                    result.put("windDirection", windDirection);
                },
                () -> {
                    result.put("success", false);
                    result.put("message", "探空数据不存在: id=" + id);
                }
        );
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/radiosonde/upload
     * 上传探空数据（支持批量上传完整垂直廓线）
     */
    @PostMapping("/upload")
    @Operation(summary = "上传探空数据")
    public ResponseEntity<Map<String, Object>> uploadSoundingData(@RequestBody Map<String, Object> request) {
        try {
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> levels = (List<Map<String, Object>>) request.getOrDefault("levels",
                    Collections.singletonList(request));

            String stationId = (String) request.getOrDefault("stationId", "UNKNOWN");
            String stationName = (String) request.getOrDefault("stationName", "未命名探空站");
            LocalDateTime launchTime = parseDateTime(request.get("launchTime"));

            List<RadiosondeData> savedList = new ArrayList<>();
            for (Map<String, Object> levelData : levels) {
                RadiosondeData data = RadiosondeData.builder()
                        .stationId(stationId)
                        .stationName(stationName)
                        .longitude(parseDouble(request.get("longitude")))
                        .latitude(parseDouble(request.get("latitude")))
                        .stationAltitude(parseDouble(request.get("stationAltitude")))
                        .launchTime(launchTime)
                        .pressureLevel(parseInt(levelData.get("pressureLevel")))
                        .geopotentialHeight(parseDouble(levelData.get("geopotentialHeight")))
                        .temperature(parseDouble(levelData.get("temperature")))
                        .dewPoint(parseDouble(levelData.get("dewPoint")))
                        .relativeHumidity(parseDouble(levelData.get("relativeHumidity")))
                        .windSpeed(parseDouble(levelData.get("windSpeed")))
                        .windDirection(parseDouble(levelData.get("windDirection")))
                        .mixingRatio(parseDouble(levelData.get("mixingRatio")))
                        .potentialTemperature(parseDouble(levelData.get("potentialTemperature")))
                        .equivalentPotentialTemperature(parseDouble(levelData.get("equivalentPotentialTemperature")))
                        .dataSource((String) request.getOrDefault("dataSource", "UPLOAD"))
                        .qualityFlag(parseDoubleOrDefault(request.get("qualityFlag"), 0.8))
                        .build();
                savedList.add(repository.save(Objects.requireNonNull(data, "data must not be null")));
            }

            log.info("探空数据上传成功: stationId={}, launchTime={}, 层数={}",
                    stationId, launchTime, savedList.size());

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("success", true);
            result.put("message", "探空数据上传成功");
            result.put("stationId", stationId);
            result.put("launchTime", launchTime != null ? launchTime.toString() : null);
            result.put("levelCount", savedList.size());
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("探空数据上传失败", e);
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("success", false);
            result.put("message", "探空数据上传失败: " + e.getMessage());
            return ResponseEntity.ok(result);
        }
    }

    private Double parseDouble(Object value) {
        if (value == null) return null;
        if (value instanceof Number n) return n.doubleValue();
        try {
            return Double.parseDouble(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Double parseDoubleOrDefault(Object value, double defaultValue) {
        Double result = parseDouble(value);
        return result != null ? result : defaultValue;
    }

    private Integer parseInt(Object value) {
        if (value == null) return null;
        if (value instanceof Number n) return n.intValue();
        try {
            return Integer.parseInt(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private LocalDateTime parseDateTime(Object value) {
        if (value == null) return LocalDateTime.now();
        if (value instanceof LocalDateTime dt) return dt;
        try {
            return LocalDateTime.parse(value.toString());
        } catch (Exception e) {
            return LocalDateTime.now();
        }
    }
}

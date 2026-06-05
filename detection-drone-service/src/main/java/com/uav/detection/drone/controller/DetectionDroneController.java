package com.uav.detection.drone.controller;

import com.uav.detection.drone.model.DetectionMission;
import com.uav.detection.drone.model.DetectionRoute;
import com.uav.detection.drone.model.DetectionSample;
import com.uav.detection.drone.model.MissionStatus;
import com.uav.detection.drone.model.MissionType;
import com.uav.detection.drone.repository.DetectionMissionRepository;
import com.uav.detection.drone.repository.DetectionRouteRepository;
import com.uav.detection.drone.repository.DetectionSampleRepository;
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

/**
 * 探测无人机 Controller
 * 管理气象探测飞行任务、航线规划和样本上传
 */
@Slf4j
@RestController
@RequestMapping("/api/detection")
@RequiredArgsConstructor
@Tag(name = "探测无人机", description = "气象探测飞行任务管理与数据采集接口")
public class DetectionDroneController {

    private final DetectionMissionRepository missionRepo;
    private final DetectionRouteRepository routeRepo;
    private final DetectionSampleRepository sampleRepo;

    // ============================================================
    // 任务管理
    // ============================================================

    /**
     * POST /api/detection/mission/create
     * 创建探测任务，自动生成航线
     */
    @PostMapping("/mission/create")
    @Operation(summary = "创建探测任务")
    public ResponseEntity<Map<String, Object>> createMission(@RequestBody Map<String, Object> request) {
        try {
            String missionType = (String) request.getOrDefault("missionType", "GRID_SCAN");
            DetectionMission mission = DetectionMission.builder()
                    .missionName((String) request.getOrDefault("missionName", "探测任务"))
                    .missionType(MissionType.valueOf(missionType))
                    .status(MissionStatus.CREATED)
                    .droneId((String) request.get("droneId"))
                    .droneName((String) request.get("droneName"))
                    .targetAreaDesc((String) request.get("targetAreaDesc"))
                    .areaMinLon(parseDouble(request.get("areaMinLon")))
                    .areaMinLat(parseDouble(request.get("areaMinLat")))
                    .areaMaxLon(parseDouble(request.get("areaMaxLon")))
                    .areaMaxLat(parseDouble(request.get("areaMaxLat")))
                    .minAltitude(parseDouble(request.get("minAltitude")))
                    .maxAltitude(parseDouble(request.get("maxAltitude")))
                    .gridResolution(parseDouble(request.get("gridResolution")))
                    .verticalLayers(parseInt(request.get("verticalLayers")))
                    .trackingTarget((String) request.get("trackingTarget"))
                    .scheduledStart(parseDateTime(request.get("scheduledStart")))
                    .notes((String) request.get("notes"))
                    .build();

            DetectionMission saved = missionRepo.save(Objects.requireNonNull(mission, "mission must not be null"));

            // 自动生成航线航点
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> waypoints =
                    (List<Map<String, Object>>) request.get("waypoints");
            if (waypoints != null && !waypoints.isEmpty()) {
                int seq = 0;
                for (Map<String, Object> wp : waypoints) {
                    DetectionRoute route = DetectionRoute.builder()
                            .missionId(saved.getId())
                            .sequenceNum(++seq)
                            .longitude(parseDouble(wp.get("longitude")))
                            .latitude(parseDouble(wp.get("latitude")))
                            .altitude(parseDouble(wp.get("altitude")))
                            .speed(parseDouble(wp.get("speed")))
                            .hoverSeconds(parseIntOrDefault(wp.get("hoverSeconds"), 0))
                            .description((String) wp.get("description"))
                            .build();
                    routeRepo.save(Objects.requireNonNull(route, "route must not be null"));
                }
            } else {
                // 自动生成网格扫描航线
                generateGridRoute(saved);
            }

            log.info("探测任务创建成功: id={}, type={}, name={}",
                    saved.getId(), saved.getMissionType(), saved.getMissionName());

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("success", true);
            result.put("message", "任务创建成功");
            result.put("missionId", saved.getId());
            result.put("routeCount", routeRepo.findByMissionIdOrderBySequenceNumAsc(saved.getId()).size());
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("创建探测任务失败", e);
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("success", false);
            result.put("message", "任务创建失败: " + e.getMessage());
            return ResponseEntity.ok(result);
        }
    }

    /**
     * GET /api/detection/mission/list?page=1&size=10&status=IN_FLIGHT
     * 分页查询任务列表
     */
    @GetMapping("/mission/list")
    @Operation(summary = "查询任务列表")
    public ResponseEntity<Map<String, Object>> listMissions(
            @RequestParam(value = "page", defaultValue = "1") Integer page,
            @RequestParam(value = "size", defaultValue = "10") Integer size,
            @RequestParam(value = "status", required = false) String status) {
        Page<DetectionMission> pageResult;
        if (status != null && !status.isBlank()) {
            List<DetectionMission> missions = missionRepo.findByStatus(MissionStatus.valueOf(status));
            int from = (page - 1) * size;
            int to = Math.min(from + size, missions.size());
            List<DetectionMission> paged = (from < missions.size()) ? missions.subList(from, to) : Collections.emptyList();
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("success", true);
            result.put("data", paged);
            result.put("total", missions.size());
            result.put("page", page);
            result.put("size", size);
            return ResponseEntity.ok(result);
        }
        pageResult = missionRepo.findAllByOrderByCreatedAtDesc(PageRequest.of(page - 1, size));
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success", true);
        result.put("data", pageResult.getContent());
        result.put("total", pageResult.getTotalElements());
        result.put("page", page);
        result.put("size", size);
        result.put("totalPages", pageResult.getTotalPages());
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/detection/mission/{id}/status
     * 获取任务详情和状态
     */
    @GetMapping("/mission/{id}/status")
    @Operation(summary = "获取任务状态")
    public ResponseEntity<Map<String, Object>> getMissionStatus(@PathVariable("id") Long id) {
        Map<String, Object> result = new LinkedHashMap<>();
        missionRepo.findById(Objects.requireNonNull(id, "id must not be null")).ifPresentOrElse(mission -> {
            List<DetectionRoute> routes = routeRepo.findByMissionIdOrderBySequenceNumAsc(id);
            result.put("success", true);
            result.put("mission", mission);
            result.put("route", routes);
            result.put("sampleCount", mission.getSampleCount());
        }, () -> {
            result.put("success", false);
            result.put("message", "任务不存在: id=" + id);
        });
        return ResponseEntity.ok(result);
    }

    /**
     * PUT /api/detection/mission/{id}/status
     * 更新任务状态
     */
    @PutMapping("/mission/{id}/status")
    @Operation(summary = "更新任务状态")
    public ResponseEntity<Map<String, Object>> updateMissionStatus(
            @PathVariable("id") Long id, @RequestBody Map<String, Object> request) {
        Map<String, Object> result = new LinkedHashMap<>();
        missionRepo.findById(Objects.requireNonNull(id, "id must not be null")).ifPresentOrElse(mission -> {
            String newStatus = (String) request.get("status");
            var status = MissionStatus.valueOf(newStatus);
            mission.setStatus(status);

            if (status == MissionStatus.IN_FLIGHT && mission.getActualStart() == null) {
                mission.setActualStart(LocalDateTime.now());
            }
            if (status == MissionStatus.LANDED) {
                mission.setActualEnd(LocalDateTime.now());
                mission.setDataOffline(true);
            }
            if (status == MissionStatus.COMPLETED) {
                mission.setDataOffline(false);
            }

            missionRepo.save(mission);
            log.info("任务状态更新: id={}, status={}", id, status);
            result.put("success", true);
            result.put("missionId", id);
            result.put("status", status);
        }, () -> {
            result.put("success", false);
            result.put("message", "任务不存在: id=" + id);
        });
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/detection/mission/{id}/data
     * 获取整条任务的全部采集数据
     */
    @GetMapping("/mission/{id}/data")
    @Operation(summary = "获取任务采集数据")
    public ResponseEntity<Map<String, Object>> getMissionData(
            @PathVariable("id") Long id,
            @RequestParam(value = "page", defaultValue = "1") Integer page,
            @RequestParam(value = "size", defaultValue = "100") Integer size) {
        Map<String, Object> result = new LinkedHashMap<>();
        missionRepo.findById(Objects.requireNonNull(id, "id must not be null")).ifPresentOrElse(mission -> {
            Page<DetectionSample> samples = sampleRepo.findByMissionId(id, PageRequest.of(page - 1, size));
            result.put("success", true);
            result.put("mission", mission);
            result.put("data", samples.getContent());
            result.put("total", samples.getTotalElements());
            result.put("page", page);
            result.put("size", size);

            // 附加统计信息
            List<Object[]> stats = sampleRepo.getMissionStatistics(id);
            if (!stats.isEmpty()) {
                Object[] s = stats.get(0);
                Map<String, Object> statMap = new LinkedHashMap<>();
                statMap.put("sampleCount", s[1]);
                statMap.put("firstSample", s[2]);
                statMap.put("lastSample", s[3]);
                statMap.put("minAltitude", s[4]);
                statMap.put("maxAltitude", s[5]);
                statMap.put("avgTemperature", s[6]);
                statMap.put("avgHumidity", s[7]);
                statMap.put("avgWindSpeed", s[8]);
                result.put("statistics", statMap);
            }
        }, () -> {
            result.put("success", false);
            result.put("message", "任务不存在: id=" + id);
        });
        return ResponseEntity.ok(result);
    }

    // ============================================================
    // 样本上传 (支持离线上传)
    // ============================================================

    /**
     * POST /api/detection/sample/upload
     * 上传采样数据 (支持单条和批量)
     */
    @PostMapping("/sample/upload")
    @Operation(summary = "上传采样数据")
    public ResponseEntity<Map<String, Object>> uploadSample(@RequestBody Map<String, Object> request) {
        try {
            boolean isBatch = request.containsKey("samples");
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> sampleList = isBatch
                    ? (List<Map<String, Object>>) request.get("samples")
                    : Collections.singletonList(request);

            Long missionId = parseLong(request.get("missionId"));
            String droneId = (String) request.get("droneId");
            boolean fromOffline = Boolean.TRUE.equals(request.get("fromOffline"));

            // 获取当前最大序号
            Integer currentMaxSeq = sampleRepo.findMaxSequenceNumByMissionId(missionId);

            List<DetectionSample> saved = new ArrayList<>();
            for (Map<String, Object> s : sampleList) {
                DetectionSample sample = DetectionSample.builder()
                        .missionId(missionId)
                        .droneId(droneId)
                        .sequenceNum(++currentMaxSeq)
                        .sampleTime(parseDateTime(s.get("sampleTime")))
                        .longitude(parseDouble(s.get("longitude")))
                        .latitude(parseDouble(s.get("latitude")))
                        .altitude(parseDouble(s.get("altitude")))
                        .temperature(parseDouble(s.get("temperature")))
                        .humidity(parseDouble(s.get("humidity")))
                        .pressure(parseDouble(s.get("pressure")))
                        .windSpeed(parseDouble(s.get("windSpeed")))
                        .windDirection(parseDouble(s.get("windDirection")))
                        .windGust(parseDouble(s.get("windGust")))
                        .visibility(parseDouble(s.get("visibility")))
                        .co2(parseDouble(s.get("co2")))
                        .pm25(parseDouble(s.get("pm25")))
                        .qualityFlag(parseDoubleOrDefault(s.get("qualityFlag"), 1.0))
                        .fromOffline(fromOffline)
                        .build();
                saved.add(sampleRepo.save(Objects.requireNonNull(sample, "sample must not be null")));
            }

            // 更新任务样本计数
            missionRepo.findById(Objects.requireNonNull(missionId, "missionId must not be null")).ifPresent(mission -> {
                mission.setSampleCount(mission.getSampleCount() + saved.size());
                mission.setDataOffline(false);  // 上传成功，清除离线标记
                missionRepo.save(mission);
            });

            log.info("样本上传成功: missionId={}, count={}, fromOffline={}",
                    missionId, saved.size(), fromOffline);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("success", true);
            result.put("message", "样本上传成功");
            result.put("missionId", missionId);
            result.put("uploadedCount", saved.size());
            result.put("fromOffline", fromOffline);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("样本上传失败", e);
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("success", false);
            result.put("message", "样本上传失败: " + e.getMessage());
            return ResponseEntity.ok(result);
        }
    }

    /**
     * GET /api/detection/sample/history?droneId=xxx&hours=24
     * 查询指定无人机历史采集数据
     */
    @GetMapping("/sample/history")
    @Operation(summary = "查询无人机历史采集数据")
    public ResponseEntity<Map<String, Object>> getSampleHistory(
            @RequestParam(value = "droneId") String droneId,
            @RequestParam(value = "hours", defaultValue = "24") Integer hours) {
        LocalDateTime since = LocalDateTime.now().minusHours(hours);
        List<DetectionSample> samples = sampleRepo.findBySampleTimeBetweenOrderBySampleTimeAsc(
                since, LocalDateTime.now());

        List<DetectionSample> filtered = samples.stream()
                .filter(s -> droneId.equals(s.getDroneId()))
                .toList();

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success", true);
        result.put("droneId", droneId);
        result.put("hours", hours);
        result.put("data", filtered);
        result.put("count", filtered.size());
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/detection/mission/{id}/vertical-profile
     * 获取垂直剖面数据 (按高度层聚合)
     */
    @GetMapping("/mission/{id}/vertical-profile")
    @Operation(summary = "获取垂直剖面数据")
    public ResponseEntity<Map<String, Object>> getVerticalProfile(
            @PathVariable("id") Long id,
            @RequestParam(value = "layerSize", defaultValue = "50") Double layerSize) {
        List<DetectionSample> samples = sampleRepo.findByMissionIdOrderBySampleTimeAsc(id);

        // 按高度分层聚合
        Map<Integer, List<DetectionSample>> layers = new LinkedHashMap<>();
        for (DetectionSample s : samples) {
            int layer = (int) (s.getAltitude() / layerSize);
            layers.computeIfAbsent(layer, k -> new ArrayList<>()).add(s);
        }

        List<Map<String, Object>> profile = new ArrayList<>();
        for (var entry : layers.entrySet().stream()
                .sorted(Map.Entry.comparingByKey()).toList()) {
            List<DetectionSample> layerSamples = entry.getValue();
            double avgAlt = layerSamples.stream().mapToDouble(DetectionSample::getAltitude).average().orElse(0);
            double avgTemp = layerSamples.stream().mapToDouble(s ->
                    s.getTemperature() != null ? s.getTemperature() : 0).average().orElse(0);
            double avgHumidity = layerSamples.stream().mapToDouble(s ->
                    s.getHumidity() != null ? s.getHumidity() : 0).average().orElse(0);
            double avgWS = layerSamples.stream().mapToDouble(s ->
                    s.getWindSpeed() != null ? s.getWindSpeed() : 0).average().orElse(0);

            Map<String, Object> layer = new LinkedHashMap<>();
            layer.put("layer", entry.getKey());
            layer.put("altitudeRange", String.format("%.0f-%.0f",
                    entry.getKey() * layerSize, (entry.getKey() + 1) * layerSize));
            layer.put("averageAltitude", Math.round(avgAlt * 100.0) / 100.0);
            layer.put("averageTemperature", Math.round(avgTemp * 100.0) / 100.0);
            layer.put("averageHumidity", Math.round(avgHumidity * 100.0) / 100.0);
            layer.put("averageWindSpeed", Math.round(avgWS * 100.0) / 100.0);
            layer.put("sampleCount", layerSamples.size());
            profile.add(layer);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success", true);
        result.put("missionId", id);
        result.put("layerSize", layerSize);
        result.put("profile", profile);
        result.put("totalSamples", samples.size());
        return ResponseEntity.ok(result);
    }

    // ============================================================
    // 航线生成辅助
    // ============================================================

    private void generateGridRoute(DetectionMission mission) {
        if (mission.getAreaMinLon() == null || mission.getAreaMaxLon() == null) {
            return;  // 无区域信息，不自动生成
        }
        double res = mission.getGridResolution() != null ? mission.getGridResolution() : 0.01;  // ~1km
        // 转换为度 (近似: 1度 ≈ 111km)
        double resDeg = res / 111000.0;

        int seq = 0;
        boolean reverse = false;
        for (double lon = mission.getAreaMinLon(); lon <= mission.getAreaMaxLon(); lon += resDeg) {
            if (reverse) {
                for (double lat = mission.getAreaMaxLat(); lat >= mission.getAreaMinLat(); lat -= resDeg) {
                    DetectionRoute route = DetectionRoute.builder()
                            .missionId(mission.getId()).sequenceNum(++seq)
                            .longitude(Math.round(lon * 1e6) / 1e6)
                            .latitude(Math.round(lat * 1e6) / 1e6)
                            .altitude(mission.getMinAltitude() != null ? mission.getMinAltitude() : 100)
                            .speed(10.0).hoverSeconds(5)
                            .description("Grid scan waypoint").build();
                    routeRepo.save(Objects.requireNonNull(route, "route must not be null"));
                }
            } else {
                for (double lat = mission.getAreaMinLat(); lat <= mission.getAreaMaxLat(); lat += resDeg) {
                    DetectionRoute route = DetectionRoute.builder()
                            .missionId(mission.getId()).sequenceNum(++seq)
                            .longitude(Math.round(lon * 1e6) / 1e6)
                            .latitude(Math.round(lat * 1e6) / 1e6)
                            .altitude(mission.getMinAltitude() != null ? mission.getMinAltitude() : 100)
                            .speed(10.0).hoverSeconds(5)
                            .description("Grid scan waypoint").build();
                    routeRepo.save(Objects.requireNonNull(route, "route must not be null"));
                }
            }
            reverse = !reverse;
        }
        log.info("自动生成网格航线: missionId={}, waypoints={}", mission.getId(), seq);
    }

    // ============================================================
    // 辅助方法
    // ============================================================

    private Double parseDouble(Object value) {
        if (value == null) return null;
        if (value instanceof Number n) return n.doubleValue();
        try { return Double.parseDouble(value.toString()); }
        catch (NumberFormatException e) { return null; }
    }

    private Double parseDoubleOrDefault(Object value, double def) {
        Double r = parseDouble(value);
        return r != null ? r : def;
    }

    private Integer parseInt(Object value) {
        if (value == null) return null;
        if (value instanceof Number n) return n.intValue();
        try { return Integer.parseInt(value.toString()); }
        catch (NumberFormatException e) { return null; }
    }

    private Integer parseIntOrDefault(Object value, int def) {
        Integer r = parseInt(value);
        return r != null ? r : def;
    }

    private Long parseLong(Object value) {
        if (value == null) return null;
        if (value instanceof Number n) return n.longValue();
        try { return Long.parseLong(value.toString()); }
        catch (NumberFormatException e) { return null; }
    }

    private LocalDateTime parseDateTime(Object value) {
        if (value == null) return LocalDateTime.now();
        if (value instanceof LocalDateTime dt) return dt;
        try { return LocalDateTime.parse(value.toString()); }
        catch (Exception e) { return LocalDateTime.now(); }
    }
}

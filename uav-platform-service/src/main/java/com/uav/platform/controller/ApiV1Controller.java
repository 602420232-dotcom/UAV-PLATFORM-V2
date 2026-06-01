package com.uav.platform.controller;

import com.uav.common.annotation.StubController;
import com.uav.common.security.JwtTokenProvider;
import com.uav.platform.dto.DataSourceRequest;
import com.uav.platform.dto.DroneRequest;
import com.uav.platform.dto.ForecastRequest;
import com.uav.platform.dto.LoginRequest;
import com.uav.platform.dto.PlanningRequest;
import com.uav.platform.dto.TaskRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 演示/联调用 API Controller
 * <p>
 * 本控制器提供模拟的 REST 端点，用于前端开发和联调测试。
 * 所有端点返回硬编码的 Mock 数据，不含真实的业务逻辑。
 * <p>
 * 计划替换：
 * - 无人机管理 → uav-platform-service 真实服务
 * - 气象服务 → meteor-forecast-service / wrf-processor-service
 * - 路径规划 → path-planning-service
 * - 数据同化 → data-assimilation-service
 * - 用户认证 → backend-spring 真实 auth 端点
 */
@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "各微服务真实 Controller",
    plannedBy = "Q3-2026"
)
@RestController
public class ApiV1Controller {

    private final JwtTokenProvider jwtTokenProvider;

    public ApiV1Controller(JwtTokenProvider jwtTokenProvider) {
        this.jwtTokenProvider = jwtTokenProvider;
    }

    /** Map builder that allows null values (unlike Map.of) */
    private static <K, V> Map<K, V> map(K k1, V v1, Object... rest) {
        Map<K, V> map = new LinkedHashMap<>();
        map.put(k1, v1);
        if (rest.length % 2 != 0) {
            throw new IllegalArgumentException("Number of arguments must be even");
        }
        for (int i = 0; i < rest.length; i += 2) {
            Object keyObj = rest[i];
            Object valueObj = rest[i + 1];
            try {
                K key = (K) keyObj;
                V value = (V) valueObj;
                map.put(key, value);
            } catch (ClassCastException e) {
                throw new IllegalArgumentException("Type mismatch in map arguments at index " + i, e);
            }
        }
        return map;
    }

    // ==================== Drones ====================
    @GetMapping("/api/v1/drones")
    public ResponseEntity<Map<String, Object>> getDrones() {
        return ResponseEntity.ok(Map.of(
            "code", 200,
            "data", List.of(
                Map.of("id", "D-001", "name", "猎鹰-1号", "model", "DJI-M300", "type", "多旋翼",
                    "maxPayload", 2.5, "maxFlightTime", 30, "maxSpeed", 15,
                    "status", "在线", "battery", 92),
                Map.of("id", "D-002", "name", "天鹰-2号", "model", "DJI-M300", "type", "多旋翼",
                    "maxPayload", 3.0, "maxFlightTime", 35, "maxSpeed", 12,
                    "status", "执行任务", "battery", 78),
                Map.of("id", "D-003", "name", "雨燕-3号", "model", "DJI-M350", "type", "多旋翼",
                    "maxPayload", 1.8, "maxFlightTime", 40, "maxSpeed", 18,
                    "status", "待命", "battery", 100)
            ),
            "message", "success"
        ));
    }

    @GetMapping("/api/v1/drones/{id}")
    public ResponseEntity<Map<String, Object>> getDrone(@PathVariable String id) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "id", id, "name", "猎鹰-1号", "model", "DJI-M300", "type", "多旋翼",
            "maxPayload", 2.5, "maxFlightTime", 30, "maxSpeed", 15,
            "status", "在线", "battery", 92
        ), "message", "success"));
    }

    @PostMapping("/api/v1/drones")
    public ResponseEntity<Map<String, Object>> createDrone(@Valid @RequestBody DroneRequest drone) {
        return ResponseEntity.ok(Map.of("code", 200, "data", drone, "message", "created"));
    }

    @PutMapping("/api/v1/drones/{id}")
    public ResponseEntity<Map<String, Object>> updateDrone(@PathVariable String id, @Valid @RequestBody DroneRequest drone) {
        return ResponseEntity.ok(Map.of("code", 200, "data", drone, "message", "updated"));
    }

    @DeleteMapping("/api/v1/drones/{id}")
    public ResponseEntity<Map<String, Object>> deleteDrone(@PathVariable String id) {
        return ResponseEntity.ok(Map.of("code", 200, "message", "deleted"));
    }

    // ==================== Tasks ====================
    @GetMapping("/api/v1/tasks")
    public ResponseEntity<Map<String, Object>> getTasks() {
        return ResponseEntity.ok(Map.of(
            "code", 200,
            "data", List.of(
                Map.of("id", "T001", "name", "市区物流配送", "type", "delivery",
                    "status", "执行中", "priority", "高", "droneId", "D-001",
                    "waypoints", List.of(
                        Map.of("lat", 39.9042, "lng", 116.4074, "order", 1, "name", "起点"),
                        Map.of("lat", 39.9142, "lng", 116.4274, "order", 2, "name", "途经点A"),
                        Map.of("lat", 39.9242, "lng", 116.4374, "order", 3, "name", "终点")
                    ),
                    "createdAt", LocalDateTime.now().minusHours(2).toString()),
                Map.of("id", "T002", "name", "电力线路巡检-A区", "type", "inspection",
                    "status", "已分配", "priority", "中", "droneId", "D-002",
                    "waypoints", List.of(
                        Map.of("lat", 39.92, "lng", 116.42, "order", 1, "name", "杆塔1"),
                        Map.of("lat", 39.93, "lng", 116.43, "order", 2, "name", "杆塔2"),
                        Map.of("lat", 39.91, "lng", 116.44, "order", 3, "name", "杆塔3")
                    ),
                    "createdAt", LocalDateTime.now().minusHours(1).toString()),
                map("id", "T003", "name", "河道巡查-B段", "type", "patrol",
                    "status", "待分配", "priority", "低", "droneId", null,
                    "waypoints", List.of(
                        Map.of("lat", 39.89, "lng", 116.38, "order", 1, "name", "巡查起点"),
                        Map.of("lat", 39.90, "lng", 116.39, "order", 2, "name", "巡查终点")
                    ),
                    "createdAt", LocalDateTime.now().minusMinutes(30).toString())
            ),
            "message", "success"
        ));
    }

    @GetMapping("/api/v1/tasks/{id}/path")
    public ResponseEntity<Map<String, Object>> getTaskPath(@PathVariable String id) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "taskId", id,
            "path", List.of(
                Map.of("lat", 39.9042, "lng", 116.4074, "altitude", 100.0),
                Map.of("lat", 39.9142, "lng", 116.4274, "altitude", 120.0),
                Map.of("lat", 39.9242, "lng", 116.4374, "altitude", 100.0)
            ),
            "totalDistance", 3240.5,
            "estimatedTime", 720,
            "noFlyZones", List.of()
        ), "message", "success"));
    }

    @PostMapping("/api/v1/tasks")
    public ResponseEntity<Map<String, Object>> createTask(@Valid @RequestBody TaskRequest task) {
        return ResponseEntity.ok(Map.of("code", 200, "data", task, "message", "created"));
    }

    @PutMapping("/api/v1/tasks/{id}")
    public ResponseEntity<Map<String, Object>> updateTask(@PathVariable String id, @Valid @RequestBody TaskRequest task) {
        return ResponseEntity.ok(Map.of("code", 200, "data", task, "message", "updated"));
    }

    @DeleteMapping("/api/v1/tasks/{id}")
    public ResponseEntity<Map<String, Object>> deleteTask(@PathVariable String id) {
        return ResponseEntity.ok(Map.of("code", 200, "message", "deleted"));
    }

    // ==================== Auth ====================
    // 🔒 SECURITY: Demo login has been disabled for security.
    // This endpoint throws UnsupportedOperationException to ensure secure authentication.
    // Use the real auth endpoint at backend-spring:8089/api/v1/auth/login for production.
    @PostMapping("/api/v1/auth/login")
    public ResponseEntity<Map<String, Object>> login(@Valid @RequestBody LoginRequest loginReq) {
        // Demo login disabled - requires real AuthenticationManager.authenticate() in production
        throw new UnsupportedOperationException(
            "Demo login disabled for security. Use the real auth endpoint at backend-spring:8089/api/v1/auth/login"
        );
    }

    @PostMapping("/api/v1/auth/logout")
    public ResponseEntity<Map<String, Object>> logout() {
        return ResponseEntity.ok(Map.of("code", 200, "message", "logout success"));
    }

    @PostMapping("/api/v1/auth/refresh")
    public ResponseEntity<Map<String, Object>> refresh(@RequestBody Map<String, Object> req) {
        try {
            String refreshToken = (String) req.get("refresh_token");
            String newToken = jwtTokenProvider.refreshAccessToken(refreshToken);
            return ResponseEntity.ok(Map.of(
                "code", 200,
                "token", newToken,
                "message", "token refreshed"
            ));
        } catch (Exception e) {
            return ResponseEntity.status(401).body(Map.of(
                "code", 401, "message", "Invalid refresh token"
            ));
        }
    }

    @GetMapping("/api/v1/auth/me")
    public ResponseEntity<Map<String, Object>> currentUser() {
        return ResponseEntity.ok(Map.of(
            "id", "U001", "username", "admin", "role", "admin", "name", "管理员"
        ));
    }

    // ==================== Weather ====================
    @GetMapping("/api/weather/sources")
    public ResponseEntity<Map<String, Object>> weatherSources() {
        return ResponseEntity.ok(Map.of("code", 200, "data", List.of(
            Map.of("id", "WS001", "name", "GFS全球预报", "type", "gfs", "resolution", "0.25°", "updateInterval", "6h"),
            Map.of("id", "WS002", "name", "ERA5再分析", "type", "era5", "resolution", "0.25°", "updateInterval", "24h"),
            Map.of("id", "WS003", "name", "地面观测站", "type", "station", "resolution", "站点", "updateInterval", "1h")
        ), "message", "success"));
    }

    @GetMapping("/api/weather/drone/{droneId}")
    public ResponseEntity<Map<String, Object>> droneWeather(@PathVariable String droneId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "droneId", droneId, "temperature", 22.8, "humidity", 58, "windSpeed", 4.5,
            "windDirection", 210, "visibility", 10000, "pressure", 1012.5,
            "timestamp", LocalDateTime.now().toString()
        ), "message", "success"));
    }

    @GetMapping("/api/weather/drone/{droneId}/history")
    public ResponseEntity<Map<String, Object>> droneWeatherHistory(@PathVariable String droneId,
            @RequestParam(defaultValue = "60") int minutes) {
        var history = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            history.add(Map.of(
                "temperature", 22.0 + Math.random() * 3, "humidity", 55 + (int)(Math.random() * 15),
                "windSpeed", 3.0 + Math.random() * 5, "timestamp", LocalDateTime.now().minusMinutes((5 - i) * 10L).toString()
            ));
        }
        return ResponseEntity.ok(Map.of("code", 200, "data", history, "message", "success"));
    }

    @GetMapping("/api/weather/fusion/{droneId}")
    public ResponseEntity<Map<String, Object>> fusionWeather(@PathVariable String droneId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "droneId", droneId, "temperature", 22.5, "humidity", 60, "windSpeed", 3.8,
            "precipitation", 0.0, "cloudCover", 35, "timestamp", LocalDateTime.now().toString()
        ), "message", "success"));
    }

    @PostMapping("/api/weather/alert")
    public ResponseEntity<Map<String, Object>> checkAlert(@RequestBody Map<String, Object> data) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "hasAlert", false, "level", "normal", "message", "当前气象条件正常"
        ), "message", "success"));
    }

    @GetMapping("/api/weather/alerts/{droneId}")
    public ResponseEntity<Map<String, Object>> getAlerts(@PathVariable String droneId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", List.of(), "message", "success"));
    }

    // ==================== Health ====================
    @GetMapping("/api/wrf/data")
    public ResponseEntity<Map<String, Object>> wrfData(@RequestParam(required = false) String fileId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "fileId", fileId != null ? fileId : "wrf_demo_001",
            "timestamp", LocalDateTime.now().toString(),
            "domain", Map.of("lat", 39.9, "lng", 116.4, "radius", 50),
            "variables", List.of("temperature", "humidity", "wind_u", "wind_v", "pressure")
        ), "message", "success"));
    }

    // ==================== Forecast ====================
    @GetMapping("/api/forecast/models")
    public ResponseEntity<Map<String, Object>> forecastModels() {
        return ResponseEntity.ok(Map.of("code", 200, "data", List.of(
            Map.of("id", "fengwu_v2", "name", "FengWu v2", "type", "AI", "variables", 69, "maxSteps", 56, "resolution", "0.25°"),
            Map.of("id", "wrf_3km", "name", "WRF 3km", "type", "NWP", "resolution", "3km", "maxHours", 72),
            Map.of("id", "era5_ensemble", "name", "ERA5 Ensemble", "type", "Reanalysis", "members", 10, "maxDays", 10)
        ), "message", "success"));
    }

    @PostMapping("/api/forecast/predict")
    public ResponseEntity<Map<String, Object>> forecastPredict(@Valid @RequestBody ForecastRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "method", req.getMethod() != null ? req.getMethod() : "fengwu",
            "predictionId", "PRED-" + UUID.randomUUID().toString().substring(0, 8),
            "status", "completed",
            "results", Map.of("temperature", 23.1, "humidity", 62, "windSpeed", 4.2)
        ), "message", "success"));
    }

    @PostMapping("/api/forecast/correct")
    public ResponseEntity<Map<String, Object>> forecastCorrect(@Valid @RequestBody ForecastRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "method", req.getMethod() != null ? req.getMethod() : "kalman",
            "corrected", true,
            "confidence", 0.87
        ), "message", "success"));
    }

    // ==================== Planning ====================
    @PostMapping("/api/planning/full")
    public ResponseEntity<Map<String, Object>> fullPlanning(@Valid @RequestBody PlanningRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "algorithm", "full",
            "planId", "PLAN-" + UUID.randomUUID().toString().substring(0, 8),
            "status", "completed",
            "route", List.of(
                Map.of("lat", 39.9042, "lng", 116.4074, "altitude", 100.0, "action", "takeoff"),
                Map.of("lat", 39.9142, "lng", 116.4174, "altitude", 120.0, "action", "cruise"),
                Map.of("lat", 39.9242, "lng", 116.4274, "altitude", 120.0, "action", "waypoint"),
                Map.of("lat", 39.9342, "lng", 116.4374, "altitude", 100.0, "action", "land")
            ),
            "totalDistance", 4100.0,
            "estimatedTime", 900,
            "energyCost", 35.2
        ), "message", "success"));
    }

    @GetMapping("/api/planning/full")
    public ResponseEntity<Map<String, Object>> fullPlanningStatus() {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of("status", "idle"), "message", "success"));
    }

    @PostMapping("/api/planning/vrptw")
    public ResponseEntity<Map<String, Object>> vrptwPlanning(@Valid @RequestBody PlanningRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "algorithm", "vrptw", "status", "completed",
            "planId", "VRPTW-" + UUID.randomUUID().toString().substring(0, 8),
            "totalDistance", 3800.0,
            "numVehicles", req.getDrones() instanceof List<?> l ? l.size() : 1
        ), "message", "success"));
    }

    @PostMapping("/api/planning/astar")
    public ResponseEntity<Map<String, Object>> astarPlanning(@Valid @RequestBody PlanningRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "algorithm", "astar", "status", "completed",
            "planId", "ASTAR-" + UUID.randomUUID().toString().substring(0, 8),
            "nodesExplored", 1250, "totalDistance", 3500.0
        ), "message", "success"));
    }

    @PostMapping("/api/planning/dwa")
    public ResponseEntity<Map<String, Object>> dwaPlanning(@Valid @RequestBody PlanningRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "algorithm", "dwa", "status", "completed",
            "planId", "DWA-" + UUID.randomUUID().toString().substring(0, 8),
            "smoothness", 0.92
        ), "message", "success"));
    }

    // ==================== Assimilation ====================
    @GetMapping("/api/assimilation/execute")
    public ResponseEntity<Map<String, Object>> assimilationExecute() {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "status", "completed", "method", "3D-VAR",
            "observationCount", 150, "timestamp", LocalDateTime.now().toString()
        ), "message", "success"));
    }

    // ==================== Monitoring ====================
    @GetMapping("/api/circuit-breaker/status")
    public ResponseEntity<Map<String, Object>> circuitBreakerStatus() {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "wrfProcessor", "CLOSED", "meteorForecast", "CLOSED",
            "pathPlanning", "CLOSED", "dataAssimilation", "CLOSED", "weatherCollector", "CLOSED"
        ), "message", "success"));
    }

    @GetMapping("/actuator/health")
    public ResponseEntity<Map<String, Object>> actuatorHealth() {
        return ResponseEntity.ok(Map.of("status", "UP"));
    }

    // ==================== Health ====================
    @GetMapping("/api/v1/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of("status", "UP", "timestamp", LocalDateTime.now().toString()));
    }
}

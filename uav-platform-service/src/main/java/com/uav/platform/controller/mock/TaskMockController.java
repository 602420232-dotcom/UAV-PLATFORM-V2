package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import com.uav.platform.dto.TaskRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "uav-platform-service 真实服务",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/v1/tasks")
public class TaskMockController {

    @SuppressWarnings("unchecked")
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

    @GetMapping
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

    @GetMapping("/{id}/path")
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

    @PostMapping
    public ResponseEntity<Map<String, Object>> createTask(@Valid @RequestBody TaskRequest task) {
        return ResponseEntity.ok(Map.of("code", 200, "data", task, "message", "created"));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Map<String, Object>> updateTask(@PathVariable String id, @Valid @RequestBody TaskRequest task) {
        return ResponseEntity.ok(Map.of("code", 200, "data", task, "message", "updated"));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, Object>> deleteTask(@PathVariable String id) {
        return ResponseEntity.ok(Map.of("code", 200, "message", "deleted"));
    }
}
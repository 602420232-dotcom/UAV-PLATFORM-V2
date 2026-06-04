package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import com.uav.platform.dto.DroneRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "uav-platform-service 真实服务",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/v1/drones")
public class DroneMockController {

    @GetMapping
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

    @GetMapping("/{id}")
    public ResponseEntity<Map<String, Object>> getDrone(@PathVariable String id) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "id", id, "name", "猎鹰-1号", "model", "DJI-M300", "type", "多旋翼",
            "maxPayload", 2.5, "maxFlightTime", 30, "maxSpeed", 15,
            "status", "在线", "battery", 92
        ), "message", "success"));
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> createDrone(@Valid @RequestBody DroneRequest drone) {
        return ResponseEntity.ok(Map.of("code", 200, "data", drone, "message", "created"));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Map<String, Object>> updateDrone(@PathVariable String id, @Valid @RequestBody DroneRequest drone) {
        return ResponseEntity.ok(Map.of("code", 200, "data", drone, "message", "updated"));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, Object>> deleteDrone(@PathVariable String id) {
        return ResponseEntity.ok(Map.of("code", 200, "message", "deleted"));
    }
}
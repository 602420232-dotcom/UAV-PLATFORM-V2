package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "monitoring-service",
    plannedBy = "Q3-2026"
)
@RestController
public class MonitoringMockController {

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

    @GetMapping("/api/v1/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of("status", "UP", "timestamp", LocalDateTime.now().toString()));
    }
}
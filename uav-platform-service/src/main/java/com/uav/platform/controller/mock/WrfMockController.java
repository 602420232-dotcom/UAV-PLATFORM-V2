package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "wrf-processor-service",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/wrf")
public class WrfMockController {

    @GetMapping("/data")
    public ResponseEntity<Map<String, Object>> wrfData(@RequestParam(required = false) String fileId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "fileId", fileId != null ? fileId : "wrf_demo_001",
            "timestamp", LocalDateTime.now().toString(),
            "domain", Map.of("lat", 39.9, "lng", 116.4, "radius", 50),
            "variables", List.of("temperature", "humidity", "wind_u", "wind_v", "pressure")
        ), "message", "success"));
    }
}
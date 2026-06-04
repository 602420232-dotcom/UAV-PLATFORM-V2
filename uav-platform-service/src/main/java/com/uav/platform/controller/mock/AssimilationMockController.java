package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "data-assimilation-service",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/assimilation")
public class AssimilationMockController {

    @GetMapping("/execute")
    public ResponseEntity<Map<String, Object>> assimilationExecute() {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "status", "completed", "method", "3D-VAR",
            "observationCount", 150, "timestamp", LocalDateTime.now().toString()
        ), "message", "success"));
    }
}
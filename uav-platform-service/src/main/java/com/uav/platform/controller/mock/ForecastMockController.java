package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import com.uav.platform.dto.ForecastRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "meteor-forecast-service",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/forecast")
public class ForecastMockController {

    @GetMapping("/models")
    public ResponseEntity<Map<String, Object>> forecastModels() {
        return ResponseEntity.ok(Map.of("code", 200, "data", List.of(
            Map.of("id", "fengwu_v2", "name", "FengWu v2", "type", "AI", "variables", 69, "maxSteps", 56, "resolution", "0.25°"),
            Map.of("id", "wrf_3km", "name", "WRF 3km", "type", "NWP", "resolution", "3km", "maxHours", 72),
            Map.of("id", "era5_ensemble", "name", "ERA5 Ensemble", "type", "Reanalysis", "members", 10, "maxDays", 10)
        ), "message", "success"));
    }

    @PostMapping("/predict")
    public ResponseEntity<Map<String, Object>> forecastPredict(@Valid @RequestBody ForecastRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "method", req.getMethod() != null ? req.getMethod() : "fengwu",
            "predictionId", "PRED-" + UUID.randomUUID().toString().substring(0, 8),
            "status", "completed",
            "results", Map.of("temperature", 23.1, "humidity", 62, "windSpeed", 4.2)
        ), "message", "success"));
    }

    @PostMapping("/correct")
    public ResponseEntity<Map<String, Object>> forecastCorrect(@Valid @RequestBody ForecastRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "method", req.getMethod() != null ? req.getMethod() : "kalman",
            "corrected", true,
            "confidence", 0.87
        ), "message", "success"));
    }
}
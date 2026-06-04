package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "meteor-forecast-service / wrf-processor-service",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/weather")
public class WeatherMockController {

    @GetMapping("/sources")
    public ResponseEntity<Map<String, Object>> weatherSources() {
        return ResponseEntity.ok(Map.of("code", 200, "data", List.of(
            Map.of("id", "WS001", "name", "GFS全球预报", "type", "gfs", "resolution", "0.25°", "updateInterval", "6h"),
            Map.of("id", "WS002", "name", "ERA5再分析", "type", "era5", "resolution", "0.25°", "updateInterval", "24h"),
            Map.of("id", "WS003", "name", "地面观测站", "type", "station", "resolution", "站点", "updateInterval", "1h")
        ), "message", "success"));
    }

    @GetMapping("/drone/{droneId}")
    public ResponseEntity<Map<String, Object>> droneWeather(@PathVariable String droneId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "droneId", droneId, "temperature", 22.8, "humidity", 58, "windSpeed", 4.5,
            "windDirection", 210, "visibility", 10000, "pressure", 1012.5,
            "timestamp", LocalDateTime.now().toString()
        ), "message", "success"));
    }

    @GetMapping("/drone/{droneId}/history")
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

    @GetMapping("/fusion/{droneId}")
    public ResponseEntity<Map<String, Object>> fusionWeather(@PathVariable String droneId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "droneId", droneId, "temperature", 22.5, "humidity", 60, "windSpeed", 3.8,
            "precipitation", 0.0, "cloudCover", 35, "timestamp", LocalDateTime.now().toString()
        ), "message", "success"));
    }

    @PostMapping("/alert")
    public ResponseEntity<Map<String, Object>> checkAlert(@RequestBody Map<String, Object> data) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "hasAlert", false, "level", "normal", "message", "当前气象条件正常"
        ), "message", "success"));
    }

    @GetMapping("/alerts/{droneId}")
    public ResponseEntity<Map<String, Object>> getAlerts(@PathVariable String droneId) {
        return ResponseEntity.ok(Map.of("code", 200, "data", List.of(), "message", "success"));
    }
}
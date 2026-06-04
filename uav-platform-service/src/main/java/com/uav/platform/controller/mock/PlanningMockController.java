package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import com.uav.platform.dto.PlanningRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "path-planning-service",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/planning")
public class PlanningMockController {

    @PostMapping("/full")
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

    @GetMapping("/full")
    public ResponseEntity<Map<String, Object>> fullPlanningStatus() {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of("status", "idle"), "message", "success"));
    }

    @PostMapping("/vrptw")
    public ResponseEntity<Map<String, Object>> vrptwPlanning(@Valid @RequestBody PlanningRequest req) {
        int numDrones = 1;
        if (req.getDrones() instanceof List<?> dronesList) {
            numDrones = dronesList.size();
        }
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "algorithm", "vrptw", "status", "completed",
            "planId", "VRPTW-" + UUID.randomUUID().toString().substring(0, 8),
            "totalDistance", 3800.0,
            "numVehicles", numDrones
        ), "message", "success"));
    }

    @PostMapping("/astar")
    public ResponseEntity<Map<String, Object>> astarPlanning(@Valid @RequestBody PlanningRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "algorithm", "astar", "status", "completed",
            "planId", "ASTAR-" + UUID.randomUUID().toString().substring(0, 8),
            "nodesExplored", 1250, "totalDistance", 3500.0
        ), "message", "success"));
    }

    @PostMapping("/dwa")
    public ResponseEntity<Map<String, Object>> dwaPlanning(@Valid @RequestBody PlanningRequest req) {
        return ResponseEntity.ok(Map.of("code", 200, "data", Map.of(
            "algorithm", "dwa", "status", "completed",
            "planId", "DWA-" + UUID.randomUUID().toString().substring(0, 8),
            "smoothness", 0.92
        ), "message", "success"));
    }
}
package com.uav.controller;
import com.uav.model.PathPlan;
import com.uav.service.PathPlanService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/path-planning")
public class PathPlanController {

    private final PathPlanService pathPlanService;

    public PathPlanController(PathPlanService pathPlanService) {
        this.pathPlanService = pathPlanService;
    }

    @GetMapping("/plans")
    public List<PathPlan> getAllPlans() {
        return pathPlanService.findAll();
    }

    @GetMapping("/plans/{id}")
    public ResponseEntity<PathPlan> getPlanById(@PathVariable Long id) {
        PathPlan plan = pathPlanService.findById(id);
        if (plan == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(plan);
    }

    @PostMapping("/plans")
    @ResponseStatus(HttpStatus.CREATED)
    public PathPlan createPlan(@RequestBody PathPlan plan) {
        return pathPlanService.create(plan);
    }

    @PutMapping("/plans/{id}")
    public ResponseEntity<PathPlan> updatePlan(@PathVariable Long id, @RequestBody PathPlan plan) {
        PathPlan updated = pathPlanService.update(id, plan);
        if (updated == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/plans/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deletePlan(@PathVariable Long id) {
        pathPlanService.delete(id);
    }

    @GetMapping("/plans/status/{status}")
    public List<PathPlan> getPlansByStatus(@PathVariable String status) {
        return pathPlanService.findByStatus(status);
    }
}

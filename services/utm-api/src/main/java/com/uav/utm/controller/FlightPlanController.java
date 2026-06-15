package com.uav.utm.controller;

import com.uav.common.core.result.Result;
import com.uav.utm.dto.SubmitFlightPlanRequest;
import com.uav.utm.entity.FlightPlan;
import com.uav.utm.service.FlightPlanService;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/flight-plans")
public class FlightPlanController {

    private final FlightPlanService flightPlanService;

    public FlightPlanController(FlightPlanService flightPlanService) {
        this.flightPlanService = flightPlanService;
    }

    @PostMapping
    @PreAuthorize("hasAuthority('utm:flightplan:write')")
    public Result<FlightPlan> submitPlan(@Valid @RequestBody SubmitFlightPlanRequest request) {
        FlightPlan plan = new FlightPlan();
        plan.setUavId(request.getUavId());
        plan.setWaypointsJson(request.getWaypoints().toString());
        plan.setPlannedStartTime(request.getPlannedStartTime());
        plan.setPlannedEndTime(request.getPlannedEndTime());
        return Result.success(flightPlanService.submitPlan(plan));
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('utm:flightplan:read')")
    public Result<FlightPlan> getPlan(@PathVariable Long id) {
        return flightPlanService.getPlan(id)
                .map(Result::success)
                .orElse(Result.error(404, "Flight plan not found"));
    }

    @PostMapping("/{id}/approve")
    @PreAuthorize("hasAuthority('utm:flightplan:write')")
    public Result<FlightPlan> approvePlan(@PathVariable Long id) {
        return Result.success(flightPlanService.approvePlan(id));
    }

    @PostMapping("/{id}/reject")
    @PreAuthorize("hasAuthority('utm:flightplan:write')")
    public Result<FlightPlan> rejectPlan(@PathVariable Long id) {
        return Result.success(flightPlanService.rejectPlan(id));
    }

    @PostMapping("/{id}/start")
    @PreAuthorize("hasAuthority('utm:flightplan:write')")
    public Result<FlightPlan> startFlight(@PathVariable Long id) {
        return Result.success(flightPlanService.startFlight(id));
    }

    @PostMapping("/{id}/complete")
    @PreAuthorize("hasAuthority('utm:flightplan:write')")
    public Result<FlightPlan> completeFlight(@PathVariable Long id) {
        return Result.success(flightPlanService.completeFlight(id));
    }

    @GetMapping
    @PreAuthorize("hasAuthority('utm:flightplan:read')")
    public Result<List<FlightPlan>> listPlans() {
        return Result.success(flightPlanService.listPlans());
    }
}

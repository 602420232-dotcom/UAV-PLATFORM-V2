package com.uav.utm.controller;

import com.uav.common.core.result.Result;
import com.uav.utm.entity.Airspace;
import com.uav.utm.service.AirspaceService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/airspaces")
public class AirspaceController {

    private final AirspaceService airspaceService;

    public AirspaceController(AirspaceService airspaceService) {
        this.airspaceService = airspaceService;
    }

    @GetMapping
    public Result<List<Airspace>> getAirspaces() {
        return Result.success(airspaceService.getAirspaces());
    }

    @PostMapping
    public Result<Airspace> createAirspace(@Valid @RequestBody Airspace airspace) {
        return Result.success(airspaceService.createDynamicAirspace(airspace));
    }

    @GetMapping("/check")
    public Result<Boolean> checkAirspaceRestriction(@RequestParam Double lon,
                                                     @RequestParam Double lat,
                                                     @RequestParam Double altitude) {
        return Result.success(airspaceService.checkAirspaceRestriction(lon, lat, altitude));
    }
}

package com.uav.weather.controller;

import com.uav.common.core.result.Result;
import com.uav.weather.dto.WeatherQueryRequest;
import com.uav.weather.dto.WindProfileQueryRequest;
import com.uav.weather.entity.WeatherGrid;
import com.uav.weather.entity.WindProfile;
import com.uav.weather.service.WeatherService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 气象数据接口
 */
@RestController
@RequestMapping("/api/v1/weather")
@RequiredArgsConstructor
@Validated
public class WeatherController {

    private final WeatherService weatherService;

    /**
     * 单点气象查询
     */
    @PostMapping("/point")
    public Result<WeatherGrid> queryPoint(@Valid @RequestBody WeatherQueryRequest request) {
        return Result.success(weatherService.queryPoint(request));
    }

    /**
     * 区域气象格点查询
     */
    @GetMapping("/region")
    public Result<List<WeatherGrid>> queryRegion(
            @RequestParam double minLon,
            @RequestParam double minLat,
            @RequestParam double maxLon,
            @RequestParam double maxLat,
            @RequestParam(required = false) Double altitude,
            @RequestParam(required = false) String source,
            @RequestParam(required = false) LocalDateTime forecastTime) {
        return Result.success(weatherService.queryRegion(minLon, minLat, maxLon, maxLat, altitude, source, forecastTime));
    }

    /**
     * 风场剖面查询
     */
    @PostMapping("/wind-profile")
    public Result<WindProfile> queryWindProfile(@Valid @RequestBody WindProfileQueryRequest request) {
        return Result.success(weatherService.queryWindProfile(request));
    }

    /**
     * 多源融合气象查询
     */
    @PostMapping("/fusion")
    public Result<WeatherGrid> queryFusion(@Valid @RequestBody WeatherQueryRequest request) {
        return Result.success(weatherService.queryFusion(request));
    }
}

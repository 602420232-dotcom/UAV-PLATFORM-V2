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
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

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
     *
     * @param request 气象查询请求
     * @return 气象格点数据
     */
    @PostMapping("/point")
    public Result<WeatherGrid> queryPoint(@Valid @RequestBody WeatherQueryRequest request) {
        return Result.success(weatherService.queryPoint(request));
    }

    /**
     * 区域气象格点查询
     *
     * @param minLon 最小经度
     * @param minLat 最小纬度
     * @param maxLon 最大经度
     * @param maxLat 最大纬度
     * @param altitude 海拔高度
     * @param source 数据源
     * @param forecastTime 预报时间
     * @return 气象格点列表
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
        return Result.success(
                weatherService.queryRegion(minLon, minLat, maxLon, maxLat, altitude, source, forecastTime));
    }

    /**
     * 风场剖面查询
     *
     * @param request 风场剖面查询请求
     * @return 风场剖面数据
     */
    @PostMapping("/wind-profile")
    public Result<WindProfile> queryWindProfile(@Valid @RequestBody WindProfileQueryRequest request) {
        return Result.success(weatherService.queryWindProfile(request));
    }

    /**
     * 多源融合气象查询
     *
     * @param request 气象查询请求
     * @return 气象格点数据
     */
    @PostMapping("/fusion")
    public Result<WeatherGrid> queryFusion(@Valid @RequestBody WeatherQueryRequest request) {
        return Result.success(weatherService.queryFusion(request));
    }
}

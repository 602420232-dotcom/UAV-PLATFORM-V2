package com.uav.weather.controller;

import com.uav.common.core.result.Result;
import com.uav.weather.dto.WeatherQueryRequest;
import com.uav.weather.dto.WindProfileQueryRequest;
import com.uav.weather.entity.WeatherGrid;
import com.uav.weather.entity.WindProfile;
import com.uav.weather.service.WeatherService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
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
@Tag(name = "气象数据", description = "气象数据查询、区域格点查询、风场剖面及多源融合")
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
    @Operation(
        summary = "单点气象查询",
        description = "根据经纬度和海拔查询指定位置的气象数据，包括温度、湿度、风速、风向、气压、能见度等。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功",
            content = @Content(schema = @Schema(implementation = WeatherGrid.class))),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping("/point")
    @PreAuthorize("hasAuthority('weather:write')")
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
    @Operation(
        summary = "区域气象格点查询",
        description = "查询指定经纬度矩形区域内的气象格点数据，支持按海拔、数据源和预报时间筛选。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功"),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @GetMapping("/region")
    @PreAuthorize("hasAuthority('weather:read')")
    public Result<List<WeatherGrid>> queryRegion(
            @Parameter(description = "最小经度", required = true, example = "116.0")
            @RequestParam double minLon,
            @Parameter(description = "最小纬度", required = true, example = "39.0")
            @RequestParam double minLat,
            @Parameter(description = "最大经度", required = true, example = "117.0")
            @RequestParam double maxLon,
            @Parameter(description = "最大纬度", required = true, example = "40.0")
            @RequestParam double maxLat,
            @Parameter(description = "海拔高度（米）", example = "100.0")
            @RequestParam(required = false) Double altitude,
            @Parameter(description = "数据源标识", example = "ECMWF")
            @RequestParam(required = false) String source,
            @Parameter(description = "预报时间", example = "2026-06-15T12:00:00")
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
    @Operation(
        summary = "风场剖面查询",
        description = "查询指定位置和高度范围内的风场剖面数据，包括不同高度层的风速和风向信息。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功",
            content = @Content(schema = @Schema(implementation = WindProfile.class))),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping("/wind-profile")
    @PreAuthorize("hasAuthority('weather:write')")
    public Result<WindProfile> queryWindProfile(@Valid @RequestBody WindProfileQueryRequest request) {
        return Result.success(weatherService.queryWindProfile(request));
    }

    /**
     * 多源融合气象查询
     *
     * @param request 气象查询请求
     * @return 气象格点数据
     */
    @Operation(
        summary = "多源融合气象查询",
        description = "融合多个气象数据源（如 ECMWF、GFS、观测站数据）的气象查询结果，提供更准确的气象场估计。"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "查询成功",
            content = @Content(schema = @Schema(implementation = WeatherGrid.class))),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未认证"),
        @ApiResponse(responseCode = "403", description = "无权限"),
    })
    @PostMapping("/fusion")
    @PreAuthorize("hasAuthority('weather:write')")
    public Result<WeatherGrid> queryFusion(@Valid @RequestBody WeatherQueryRequest request) {
        return Result.success(weatherService.queryFusion(request));
    }
}

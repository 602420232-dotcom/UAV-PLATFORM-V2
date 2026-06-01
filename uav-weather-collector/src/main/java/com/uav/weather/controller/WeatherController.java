package com.uav.weather.controller;
import com.uav.common.exception.BusinessException;
import com.uav.weather.model.WeatherData;
import com.uav.weather.service.WeatherCollectorService;
import org.springframework.validation.annotation.Validated;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/weather")
@Validated
public class WeatherController {

    @Resource
    private WeatherCollectorService weatherService;

    @PostMapping("/collect/uav")
    public Map<String, Object> collectFromUAV(@Valid @RequestBody Map<String, Object> sensorData) {
        // 基本数据验证
        if (sensorData == null || sensorData.isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "传感器数据不能为空");
        }
        return weatherService.collectFromUAVSensor(sensorData);
    }

    @PostMapping("/collect/wrf")
    public Map<String, Object> collectFromWRF(@Valid @RequestBody Map<String, Object> wrfData) {
        if (wrfData == null || wrfData.isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "WRF数据不能为空");
        }
        return weatherService.collectFromWRFModel(wrfData);
    }

    @PostMapping("/collect/ground")
    public Map<String, Object> collectFromGroundStation(@Valid @RequestBody Map<String, Object> stationData) {
        if (stationData == null || stationData.isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "地面站数据不能为空");
        }
        return weatherService.collectFromGroundStation(stationData);
    }

    @GetMapping("/drone/{droneId}")
    public Map<String, Object> getDroneWeather(
            @PathVariable @NotBlank @Pattern(regexp = "^[a-zA-Z0-9_-]+$", message = "无效的无人机ID格式") String droneId) {
        return weatherService.getCurrentWeather(droneId);
    }

    @GetMapping("/drone/{droneId}/history")
    public List<Map<String, Object>> getDroneWeatherHistory(
            @PathVariable @NotBlank @Pattern(regexp = "^[a-zA-Z0-9_-]+$", message = "无效的无人机ID格式") String droneId,
            @RequestParam(defaultValue = "10") @Min(value = 1, message = "时间范围最小为1分钟") @Max(value = 1440, message = "时间范围最大为1440分钟（24小时）") int minutes) {
        return weatherService.getWeatherHistory(droneId, minutes);
    }

    @GetMapping("/fusion/{droneId}")
    public Map<String, Object> getFusedWeather(
            @PathVariable @NotBlank @Pattern(regexp = "^[a-zA-Z0-9_-]+$", message = "无效的无人机ID格式") String droneId) {
        return weatherService.getFusedWeather(droneId);
    }

    @PostMapping("/alert")
    public Map<String, Object> checkAlert(@Valid @RequestBody Map<String, Object> weatherData) {
        if (weatherData == null || weatherData.isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "气象数据不能为空");
        }
        return weatherService.evaluateAlert(weatherData);
    }

    @GetMapping("/alerts/{droneId}")
    public List<Map<String, Object>> getAlerts(
            @PathVariable @NotBlank @Pattern(regexp = "^[a-zA-Z0-9_-]+$", message = "无效的无人机ID格式") String droneId) {
        return weatherService.getDroneAlerts(droneId);
    }

    @GetMapping("/sources")
    public List<Map<String, Object>> getAvailableSources() {
        return weatherService.listDataSources();
    }
}

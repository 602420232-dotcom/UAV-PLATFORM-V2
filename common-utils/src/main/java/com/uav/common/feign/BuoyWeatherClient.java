package com.uav.common.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import java.util.Map;

/**
 * 浮标气象服务Feign Client
 * 用于声明式调用浮标气象数据服务
 * 
 * ⚠️ 未来扩展占位符
 * 对应服务 buoy-weather-service 模块尚不存在，当前保留作为架构扩展点。
 * 
 * 注意事项：
 * 1. 此 FeignClient 目前不会被实际调用（无对应服务实例）
 * 2. 当未来实现 buoy-weather-service 时，需确保服务名和端点路径与此定义一致
 * 3. 移除前需确认无其他模块注入此 Client
 *
 * @see WeatherCollectorCircuitBreakerService 使用了此 Client 但配置了熔断保护
 */
@FeignClient(name = "buoy-weather-service", url = "${services.buoy-weather.url:http://buoy-weather:8084}",
        fallback = BuoyWeatherClientFallback.class)
public interface BuoyWeatherClient {

    /**
     * 获取浮标数据
     *
     * @param buoyId 浮标ID
     * @return 浮标数据
     */
    @GetMapping("/api/buoy/data")
    Map<String, Object> getBuoyData(@RequestParam(value = "buoyId", required = false) String buoyId);

    /**
     * 获取浮标列表
     * 
     * @param page 页码
     * @param size 每页数量
     * @return 浮标列表
     */
    @GetMapping("/api/buoy/list")
    Map<String, Object> listBuoys(@RequestParam(value = "page", defaultValue = "1") Integer page,
                                  @RequestParam(value = "size", defaultValue = "10") Integer size);

    /**
     * 获取浮标详情
     * 
     * @param id 浮标ID
     * @return 浮标详情
     */
    @GetMapping("/api/buoy/{id}")
    Map<String, Object> getBuoyDetail(@PathVariable("id") Long id);

    /**
     * 获取浮标实时数据
     * 
     * @param buoyId 浮标ID
     * @return 实时数据
     */
    @GetMapping("/api/buoy/realtime")
    Map<String, Object> getRealtimeData(@RequestParam(value = "buoyId") String buoyId);

    /**
     * 上传浮标数据
     * 
     * @param request 浮标数据请求
     * @return 上传结果
     */
    @PostMapping("/api/buoy/upload")
    Map<String, Object> uploadBuoyData(@RequestBody Map<String, Object> request);

    /**
     * 健康检查
     */
    @GetMapping("/actuator/health")
    Map<String, Object> health();
}

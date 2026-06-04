package com.uav.common.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import java.util.Map;

/**
 * 卫星气象服务Feign Client
 * 用于声明式调用卫星气象数据服务
 * 
 * ⚠️ 未来扩展占位符
 * 对应服务 satellite-weather-service 模块尚不存在，当前保留作为架构扩展点。
 * 
 * 注意事项：
 * 1. 此 FeignClient 目前不会被实际调用（无对应服务实例）
 * 2. 当未来实现 satellite-weather-service 时，需确保服务名和端点路径与此定义一致
 * 3. 移除前需确认无其他模块注入此 Client
 *
 * @see WeatherCollectorCircuitBreakerService 使用了此 Client 但配置了熔断保护
 */
@FeignClient(name = "satellite-weather-service", url = "${services.satellite-weather.url:http://satellite-weather:8082}",
        fallback = SatelliteWeatherClientFallback.class)
public interface SatelliteWeatherClient {

    /**
     * 获取卫星云图数据
     *
     * @param region 区域范围 (如: CHINA, ASIA, GLOBAL)
     * @param channel 波段通道 (如: IR, VIS, WV)
     * @return 卫星云图数据
     */
    @GetMapping("/api/satellite/cloud")
    Map<String, Object> getCloudImage(@RequestParam(value = "region", defaultValue = "CHINA") String region,
                                      @RequestParam(value = "channel", defaultValue = "IR") String channel);

    /**
     * 获取卫星云图列表
     * 
     * @param page 页码
     * @param size 每页数量
     * @return 卫星云图列表
     */
    @GetMapping("/api/satellite/list")
    Map<String, Object> listSatelliteImages(@RequestParam(value = "page", defaultValue = "1") Integer page,
                                            @RequestParam(value = "size", defaultValue = "10") Integer size);

    /**
     * 获取卫星云图详情
     * 
     * @param id 云图ID
     * @return 云图详情
     */
    @GetMapping("/api/satellite/{id}")
    Map<String, Object> getSatelliteImageDetail(@PathVariable("id") Long id);

    /**
     * 上传卫星数据
     * 
     * @param request 卫星数据请求
     * @return 上传结果
     */
    @PostMapping("/api/satellite/upload")
    Map<String, Object> uploadSatelliteData(@RequestBody Map<String, Object> request);

    /**
     * 健康检查
     */
    @GetMapping("/actuator/health")
    Map<String, Object> health();
}

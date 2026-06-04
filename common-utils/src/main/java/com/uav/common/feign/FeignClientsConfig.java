package com.uav.common.feign;

import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Configuration;

/**
 * Feign Clients统一配置
 * 
 * 启用FeignClients扫描，配置全局默认选项。
 * 
 * 使用方法：
 * 在主应用类添加 @EnableFeignClients 或在此处指定扫描包路径。
 * 
 * 各服务只需在application.yml中配置服务URL即可使用。
 */
@Configuration
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class FeignClientsConfig {
    
    /**
     * 全局Feign配置属性示例
     * 
     * 可在application.yml中通过以下方式覆盖：
     * 
     * feign:
     *   client:
     *     config:
     *       default:
     *         connectTimeout: 5000
     *         readTimeout: 10000
     *         loggerLevel: basic
     * 
     * 或针对特定服务：
     * 
     * feign:
     *   client:
     *     config:
     *       path-planning-service:
     *         connectTimeout: 3000
     *         readTimeout: 5000
     */
}

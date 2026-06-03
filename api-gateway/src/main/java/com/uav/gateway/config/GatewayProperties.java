package com.uav.gateway.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * API 网关配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "gateway")
public class GatewayProperties {
    // 目前没有特定的配置，但为未来扩展
}

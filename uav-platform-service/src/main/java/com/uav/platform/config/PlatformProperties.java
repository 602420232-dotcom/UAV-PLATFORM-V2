package com.uav.platform.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * UAV 平台服务配置属性
 */
@Configuration
@ConfigurationProperties(prefix = "platform")
public class PlatformProperties {
    // 目前没有特定的配置，但为未来扩展
}

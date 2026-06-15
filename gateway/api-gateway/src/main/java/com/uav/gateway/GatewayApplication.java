package com.uav.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * API Gateway Application
 * UAV Platform API Gateway - Entry point for all microservices
 *
 * Note: @EnableDiscoveryClient removed for standalone/local builds.
 * Nacos discovery is disabled by default in application.yml.
 * Re-enable by setting spring.cloud.nacos.discovery.enabled=true when Nacos is available.
 */
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import com.uav.gateway.config.V1PathMappingConfig;

@SpringBootApplication(scanBasePackages = {"com.uav.gateway"})
@EnableConfigurationProperties(V1PathMappingConfig.class)
public class GatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}

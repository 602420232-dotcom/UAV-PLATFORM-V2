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
@SpringBootApplication(scanBasePackages = {"com.uav.gateway"})
public class GatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}

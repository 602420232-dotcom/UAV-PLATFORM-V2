package com.uav.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

/**
 * API Gateway Application
 * UAV Platform API Gateway - Entry point for all microservices
 */
@EnableDiscoveryClient
@SpringBootApplication(scanBasePackages = {"com.uav.gateway", "com.uav.common"})
public class GatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}

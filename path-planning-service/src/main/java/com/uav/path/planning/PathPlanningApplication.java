package com.uav.path.planning;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication(scanBasePackages = {"com.uav.path.planning", "com.uav.common"})
@EnableDiscoveryClient
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class PathPlanningApplication {
    public static void main(String[] args) {
        SpringApplication.run(PathPlanningApplication.class, args);
    }
}

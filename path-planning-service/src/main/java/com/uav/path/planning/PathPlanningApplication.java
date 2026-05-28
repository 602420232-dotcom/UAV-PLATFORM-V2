package com.uav.path.planning;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;

@SpringBootApplication(scanBasePackages = {"com.uav.path.planning", "com.uav.common"})
@ComponentScan(
    basePackages = {"com.uav.path.planning", "com.uav.common"},
    excludeFilters = @ComponentScan.Filter(
        type = FilterType.REGEX,
        pattern = "com.uav.common.exception.*"
    )
)
@EnableDiscoveryClient
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class PathPlanningApplication {
    public static void main(String[] args) {
        SpringApplication.run(PathPlanningApplication.class, args);
    }
}

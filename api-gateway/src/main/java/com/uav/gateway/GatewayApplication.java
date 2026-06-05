package com.uav.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@ComponentScan(
    basePackages = "com.uav",
    excludeFilters = {
        @ComponentScan.Filter(
            type = FilterType.REGEX,
            pattern = "com\\.uav\\.common\\.exception\\..*"
        ),
        @ComponentScan.Filter(
            type = FilterType.REGEX,
            pattern = "com\\.uav\\.common\\.security\\.JwtAuthenticationFilter"
        )
    }
)
@EnableDiscoveryClient
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}

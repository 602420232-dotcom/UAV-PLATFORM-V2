package com.uav;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@ComponentScan(basePackages = "com.uav", excludeFilters = {
    @ComponentScan.Filter(type = FilterType.REGEX, pattern = "com\\.uav\\.common\\.exception\\.GlobalExceptionHandler"),
    @ComponentScan.Filter(type = FilterType.REGEX, pattern = "com\\.uav\\.common\\.config\\.RedisConfig"),
    @ComponentScan.Filter(type = FilterType.REGEX, pattern = "com\\.uav\\.common\\.config\\.CommonSecurityConfig"),
    @ComponentScan.Filter(type = FilterType.REGEX, pattern = "com\\.uav\\.common\\.security\\.JwtSecurityConfig"),
    @ComponentScan.Filter(type = FilterType.REGEX, pattern = "com\\.uav\\.common\\.resilience\\..*"),
    @ComponentScan.Filter(type = FilterType.REGEX, pattern = "com\\.uav\\.config\\.Resilience4jConfig")
})
@EnableCaching
@EnableScheduling
public class UavPathPlanningApplication {
    public static void main(String[] args) {
        SpringApplication.run(UavPathPlanningApplication.class, args);
    }
}
package com.uav.meteor.forecast;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;

@SpringBootApplication(scanBasePackages = {"com.uav.meteor.forecast", "com.uav.common"})
@ComponentScan(
    basePackages = {"com.uav.meteor.forecast", "com.uav.common"},
    excludeFilters = @ComponentScan.Filter(
        type = FilterType.REGEX,
        pattern = "com.uav.common.exception.*"
    )
)
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class MeteorForecastApplication {
    public static void main(String[] args) {
        SpringApplication.run(MeteorForecastApplication.class, args);
    }
}

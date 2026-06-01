package com.uav.meteor.forecast;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication(scanBasePackages = {"com.uav.meteor.forecast", "com.uav.common"})
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class MeteorForecastApplication {
    public static void main(String[] args) {
        SpringApplication.run(MeteorForecastApplication.class, args);
    }
}

package com.uav.weather;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication(scanBasePackages = {"com.uav.weather", "com.uav.common"})
@EnableScheduling
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class WeatherCollectorApplication {
    public static void main(String[] args) {
        SpringApplication.run(WeatherCollectorApplication.class, args);
    }
}

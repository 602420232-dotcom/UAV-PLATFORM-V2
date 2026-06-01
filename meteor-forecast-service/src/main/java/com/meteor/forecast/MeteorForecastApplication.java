package com.meteor.forecast;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class MeteorForecastApplication {
    public static void main(String[] args) {
        SpringApplication.run(MeteorForecastApplication.class, args);
    }
}
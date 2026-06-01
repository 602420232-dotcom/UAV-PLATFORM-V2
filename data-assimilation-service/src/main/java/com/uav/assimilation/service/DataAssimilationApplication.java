package com.uav.assimilation.service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication(scanBasePackages = {"com.uav.assimilation.service", "com.uav.common"})
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class DataAssimilationApplication {
    public static void main(String[] args) {
        SpringApplication.run(DataAssimilationApplication.class, args);
    }
}

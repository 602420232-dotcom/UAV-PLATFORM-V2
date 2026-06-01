package com.uav.wrf.processor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication(scanBasePackages = {"com.uav.wrf.processor", "com.uav.common"})
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class WrfProcessorApplication {
    public static void main(String[] args) {
        SpringApplication.run(WrfProcessorApplication.class, args);
    }
}

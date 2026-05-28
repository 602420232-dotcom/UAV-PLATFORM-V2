package com.uav.wrf.processor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;

@SpringBootApplication(scanBasePackages = {"com.uav.wrf.processor", "com.uav.common"})
@ComponentScan(
    basePackages = {"com.uav.wrf.processor", "com.uav.common"},
    excludeFilters = @ComponentScan.Filter(
        type = FilterType.REGEX,
        pattern = "com.uav.common.exception.*"
    )
)
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class WrfProcessorApplication {
    public static void main(String[] args) {
        SpringApplication.run(WrfProcessorApplication.class, args);
    }
}

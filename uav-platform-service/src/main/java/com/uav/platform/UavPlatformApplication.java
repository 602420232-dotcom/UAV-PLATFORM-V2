package com.uav.platform;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication(scanBasePackages = "com.uav")
@ComponentScan(
    basePackages = "com.uav",
    excludeFilters = @ComponentScan.Filter(
        type = FilterType.REGEX,
        pattern = "com.uav.common.exception.*"
    )
)
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class UavPlatformApplication {
    
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    public static void main(String[] args) {
        SpringApplication.run(UavPlatformApplication.class, args);
    }
}

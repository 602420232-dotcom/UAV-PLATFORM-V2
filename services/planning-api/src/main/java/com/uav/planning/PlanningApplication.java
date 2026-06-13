package com.uav.planning;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication(scanBasePackages = {"com.uav.planning", "com.uav.common"})
@EnableAsync
public class PlanningApplication {

    public static void main(String[] args) {
        SpringApplication.run(PlanningApplication.class, args);
    }
}

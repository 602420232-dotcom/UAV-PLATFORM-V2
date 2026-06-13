package com.uav.assimilation;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = {"com.uav.assimilation", "com.uav.common"})
public class AssimilationApplication {

    public static void main(String[] args) {
        SpringApplication.run(AssimilationApplication.class, args);
    }
}

package com.uav.observation;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = {"com.uav.observation", "com.uav.common"})
public class ObservationApplication {

    public static void main(String[] args) {
        SpringApplication.run(ObservationApplication.class, args);
    }
}

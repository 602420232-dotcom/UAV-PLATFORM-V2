package com.bayesian.exception;

public class DegradedModeException extends RuntimeException {

    private final String serviceName;

    public DegradedModeException(String serviceName, String message) {
        super(message);
        this.serviceName = serviceName;
    }

    public String getServiceName() {
        return serviceName;
    }
}

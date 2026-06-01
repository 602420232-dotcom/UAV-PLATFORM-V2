package com.bayesian.exception;

public class AssimilationException extends RuntimeException {

    private final int statusCode;

    public AssimilationException(String message) {
        super(message);
        this.statusCode = 500;
    }

    public AssimilationException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    public AssimilationException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 500;
    }

    public int getStatusCode() {
        return statusCode;
    }
}

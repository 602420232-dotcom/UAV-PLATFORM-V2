package com.bayesian.service;

import com.bayesian.client.PythonServiceClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class PythonService {

    private final PythonServiceClient pythonClient;

    @Value("${python.service.url:http://localhost:8000}")
    private String pythonServiceUrl;

    public PythonService(PythonServiceClient pythonClient) {
        this.pythonClient = pythonClient;
    }

    public String executeAssimilation(Object request) {
        return pythonClient.executeAssimilation(pythonServiceUrl, request);
    }
}

package com.uav.bayesian.controller;
import com.uav.bayesian.service.VarianceFieldService;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/variance")
public class VarianceFieldController {

    private final VarianceFieldService varianceFieldService;

    public VarianceFieldController(VarianceFieldService varianceFieldService) {
        this.varianceFieldService = varianceFieldService;
    }

    @PostMapping("/compute")
    public ResponseEntity<Map<String, Object>> computeVariance(@RequestBody Map<String, Object> request) {
        return ResponseEntity.ok(varianceFieldService.computeVariance(request));
    }
}

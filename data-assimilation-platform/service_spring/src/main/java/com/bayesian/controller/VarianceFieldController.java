package com.bayesian.controller;
import com.bayesian.service.VarianceFieldService;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

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

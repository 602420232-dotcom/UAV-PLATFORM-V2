package com.uav.bayesian.controller;
import com.uav.bayesian.service.AssimilationService;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/assimilation")
public class AssimilationController {

    private final AssimilationService assimilationService;

    public AssimilationController(AssimilationService assimilationService) {
        this.assimilationService = assimilationService;
    }

    @PostMapping("/execute")
    public ResponseEntity<Map<String, Object>> execute(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = assimilationService.executeAssimilation(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/status/{jobId}")
    public ResponseEntity<Object> getStatus(@PathVariable String jobId) {
        return ResponseEntity.ok(assimilationService.getJobStatus(jobId));
    }
}

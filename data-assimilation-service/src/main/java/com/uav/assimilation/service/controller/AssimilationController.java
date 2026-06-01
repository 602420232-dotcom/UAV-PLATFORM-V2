package com.uav.assimilation.service.controller;
import com.uav.common.dto.AssimilationRequest;
import com.uav.common.script.PythonScriptInvoker;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/assimilation")
public class AssimilationController {

    private final PythonScriptInvoker pythonScriptInvoker;

    @Value("${assimilation.python-script}")
    private String pythonScriptPath;

    public AssimilationController(PythonScriptInvoker pythonScriptInvoker) {
        this.pythonScriptInvoker = pythonScriptInvoker;
    }

    @PostMapping("/execute")
    public Map<String, Object> execute(@Valid @RequestBody AssimilationRequest request) {
        Map<String, Object> params = Map.of(
            "algorithm", request.getAlgorithm(),
            "background", request.getBackground(),
            "observations", request.getObservations(),
            "config", request.getConfig()
        );
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "execute", params);
    }

    @PostMapping("/variance")
    public Map<String, Object> getVariance(@Valid @RequestBody AssimilationRequest request) {
        Map<String, Object> params = Map.of(
            "algorithm", request.getAlgorithm(),
            "background", request.getBackground(),
            "observations", request.getObservations(),
            "config", request.getConfig()
        );
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "variance", params);
    }

    @PostMapping("/batch")
    public Map<String, Object> batchProcess(@Valid @RequestBody AssimilationRequest request) {
        Map<String, Object> params = Map.of(
            "algorithm", request.getAlgorithm(),
            "background", request.getBackground(),
            "observations", request.getObservations(),
            "config", request.getConfig()
        );
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "batch", params);
    }
}

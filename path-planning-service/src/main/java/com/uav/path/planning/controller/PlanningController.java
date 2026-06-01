package com.uav.path.planning.controller;
import com.uav.common.dto.PathPlanningRequest;
import com.uav.common.script.PythonScriptInvoker;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/planning")
public class PlanningController {

    private final PythonScriptInvoker pythonScriptInvoker;

    @Value("${planning.python-script}")
    private String pythonScriptPath;

    public PlanningController(PythonScriptInvoker pythonScriptInvoker) {
        this.pythonScriptInvoker = pythonScriptInvoker;
    }

    @PostMapping("/vrptw")
    public Map<String, Object> vrptw(@Valid @RequestBody PathPlanningRequest request) {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "vrptw", toParams(request));
    }

    @PostMapping("/astar")
    public Map<String, Object> astar(@Valid @RequestBody PathPlanningRequest request) {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "astar", toParams(request));
    }

    @PostMapping("/dwa")
    public Map<String, Object> dwa(@Valid @RequestBody PathPlanningRequest request) {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "dwa", toParams(request));
    }

    @PostMapping("/full")
    public Map<String, Object> full(@Valid @RequestBody PathPlanningRequest request) {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "full", toParams(request));
    }

    private Map<String, Object> toParams(PathPlanningRequest request) {
        return Map.of(
            "algorithm", request.getAlgorithm(),
            "drones", request.getDrones(),
            "tasks", request.getTasks(),
            "weatherData", request.getWeatherData(),
            "constraints", request.getConstraints()
        );
    }
}

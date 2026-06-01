package com.path.planning.controller;
import com.uav.common.dto.PathPlanningRequest;
import com.uav.common.utils.PythonScriptInvoker;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

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
        return pythonScriptInvoker.execute(pythonScriptPath, "vrptw", toParams(request));
    }

    @PostMapping("/astar")
    public Map<String, Object> astar(@Valid @RequestBody PathPlanningRequest request) {
        return pythonScriptInvoker.execute(pythonScriptPath, "astar", toParams(request));
    }

    @PostMapping("/dwa")
    public Map<String, Object> dwa(@Valid @RequestBody PathPlanningRequest request) {
        return pythonScriptInvoker.execute(pythonScriptPath, "dwa", toParams(request));
    }

    @PostMapping("/full")
    public Map<String, Object> full(@Valid @RequestBody PathPlanningRequest request) {
        return pythonScriptInvoker.execute(pythonScriptPath, "full", toParams(request));
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

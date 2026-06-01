package com.uav.meteor.forecast.controller;
import com.uav.common.dto.ForecastRequest;
import com.uav.common.script.PythonScriptInvoker;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/forecast")
public class ForecastController {

    private final PythonScriptInvoker pythonScriptInvoker;

    @Value("${forecast.python-script}")
    private String pythonScriptPath;

    public ForecastController(PythonScriptInvoker pythonScriptInvoker) {
        this.pythonScriptInvoker = pythonScriptInvoker;
    }

    @PostMapping("/predict")
    public Map<String, Object> predict(@Valid @RequestBody ForecastRequest request) {
        Map<String, Object> params = Map.of(
            "method", request.getMethod(),
            "data", request.getData(),
            "config", request.getConfig()
        );
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "predict", params);
    }

    @PostMapping("/correct")
    public Map<String, Object> correct(@Valid @RequestBody ForecastRequest request) {
        Map<String, Object> params = Map.of(
            "method", request.getMethod(),
            "data", request.getData(),
            "config", request.getConfig()
        );
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "correct", params);
    }

    @GetMapping("/models")
    public Map<String, Object> getModels() {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "model_info", Map.of());
    }

    @GetMapping("/get")
    public Map<String, Object> getForecast(@RequestParam Double lat, @RequestParam Double lng, @RequestParam Integer hours) {
        Map<String, Object> params = Map.of(
            "lat", lat,
            "lng", lng,
            "hours", hours
        );
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "get_forecast", params);
    }

    @PostMapping("/detail")
    public Map<String, Object> getDetailedForecast(@RequestBody Map<String, Object> request) {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "get_detailed_forecast", request);
    }

    @GetMapping("/realtime")
    public Map<String, Object> getRealtimeWeather(@RequestParam Double lat, @RequestParam Double lng) {
        Map<String, Object> params = Map.of(
            "lat", lat,
            "lng", lng
        );
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "get_realtime_weather", params);
    }
    
    @PostMapping("/train")
    public Map<String, Object> trainModel(@RequestBody Map<String, Object> request) {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "train_full", request);
    }
    
    @PostMapping("/improve")
    public Map<String, Object> improveModel(@RequestBody Map<String, Object> request) {
        return pythonScriptInvoker.executeAsMap(pythonScriptPath, "improve", request);
    }
    
    @PostMapping("/save")
    public Map<String, Object> saveModels(@RequestBody(required = false) Map<String, String> request) {
        String version = request != null ? request.get("version") : null;
        if (version != null) {
            return pythonScriptInvoker.executeAsMap(pythonScriptPath, "save_models", Map.of("version", version));
        } else {
            return pythonScriptInvoker.executeAsMap(pythonScriptPath, "save_models", Map.of());
        }
    }
    
    @PostMapping("/load")
    public Map<String, Object> loadModels(@RequestBody(required = false) Map<String, String> request) {
        String version = request != null ? request.get("version") : null;
        if (version != null) {
            return pythonScriptInvoker.executeAsMap(pythonScriptPath, "load_models", Map.of("version", version));
        } else {
            return pythonScriptInvoker.executeAsMap(pythonScriptPath, "load_models", Map.of());
        }
    }
}

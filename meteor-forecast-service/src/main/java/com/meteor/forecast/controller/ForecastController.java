package com.meteor.forecast.controller;
import com.uav.common.dto.ForecastRequest;
import com.uav.common.utils.PythonScriptInvoker;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

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
        return pythonScriptInvoker.execute(pythonScriptPath, "predict", params);
    }

    @PostMapping("/correct")
    public Map<String, Object> correct(@Valid @RequestBody ForecastRequest request) {
        Map<String, Object> params = Map.of(
            "method", request.getMethod(),
            "data", request.getData(),
            "config", request.getConfig()
        );
        return pythonScriptInvoker.execute(pythonScriptPath, "correct", params);
    }

    @GetMapping("/models")
    public Map<String, Object> getModels() {
        return Map.of(
            "success", true,
            "data", Map.of("lstm_model", "LSTM时间序列预测模型", "xgb_model", "XGBoost数据订正模型")
        );
    }
}

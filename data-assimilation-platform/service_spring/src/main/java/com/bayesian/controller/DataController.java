package com.bayesian.controller;
import org.springframework.http.ResponseEntity;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @GetMapping("/sources")
    public ResponseEntity<Map<String, Object>> listSources() {
        return ResponseEntity.ok(Map.of(
                "sources", java.util.List.of(
                        Map.of("id", "satellite", "name", "卫星数据"),
                        Map.of("id", "radar", "name", "雷达数据"),
                        Map.of("id", "ground", "name", "地面站数据")
                )
        ));
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, String>> status() {
        return ResponseEntity.ok(Map.of("status", "connected", "type", "data-service"));
    }
}

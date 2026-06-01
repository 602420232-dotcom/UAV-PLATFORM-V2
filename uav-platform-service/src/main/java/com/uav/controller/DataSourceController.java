package com.uav.controller;
import com.uav.config.SecurityAuditConfig;
import com.uav.common.exception.DataNotFoundException;
import com.uav.platform.dto.DataSourceRequest;
import com.uav.service.DataSourceService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/data-sources")
public class DataSourceController {

    private final DataSourceService dataSourceService;
    private final SecurityAuditConfig securityAuditConfig;

    public DataSourceController(DataSourceService dataSourceService,
                                SecurityAuditConfig securityAuditConfig) {
        this.dataSourceService = dataSourceService;
        this.securityAuditConfig = securityAuditConfig;
    }

    @GetMapping
    public ResponseEntity<Map<String, Object>> getDataSourceList() {
        String username = securityAuditConfig.getCurrentUsername();
        List<Map<String, Object>> dataSources = dataSourceService.listDataSources();
        securityAuditConfig.logUserActivity(username, "获取数据源列表", "成功获取数据源列表");
        return ResponseEntity.ok(Map.of("code", 200, "message", "获取数据源列表成功", "data", dataSources));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Map<String, Object>> getDataSourceById(@PathVariable Long id) {
        String username = securityAuditConfig.getCurrentUsername();
        Map<String, Object> dataSource = dataSourceService.getDataSourceById(id);
        if (dataSource == null) {
            throw new DataNotFoundException("DataSource", id);
        }
        securityAuditConfig.logUserActivity(username, "获取数据源详情", "成功获取数据源ID: " + id);
        return ResponseEntity.ok(Map.of("code", 200, "message", "获取数据源详情成功", "data", dataSource));
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> createDataSource(@Valid @RequestBody DataSourceRequest requestBody) {
        String username = securityAuditConfig.getCurrentUsername();
        Map<String, Object> dataSource = dataSourceService.createDataSource(toMap(requestBody));
        securityAuditConfig.logUserActivity(username, "创建数据源", "成功创建数据源: " + requestBody.getName());
        return ResponseEntity.ok(Map.of("code", 200, "message", "创建数据源成功", "data", dataSource));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Map<String, Object>> updateDataSource(@PathVariable Long id, @Valid @RequestBody DataSourceRequest requestBody) {
        String username = securityAuditConfig.getCurrentUsername();
        Map<String, Object> dataSource = dataSourceService.updateDataSource(id, toMap(requestBody));
        if (dataSource == null) {
            throw new DataNotFoundException("DataSource", id);
        }
        securityAuditConfig.logUserActivity(username, "更新数据源", "成功更新数据源ID: " + id);
        return ResponseEntity.ok(Map.of("code", 200, "message", "更新数据源成功", "data", dataSource));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, Object>> deleteDataSource(@PathVariable Long id) {
        String username = securityAuditConfig.getCurrentUsername();
        boolean success = dataSourceService.deleteDataSource(id);
        if (!success) {
            throw new DataNotFoundException("DataSource", id);
        }
        securityAuditConfig.logUserActivity(username, "删除数据源", "成功删除数据源ID: " + id);
        return ResponseEntity.ok(Map.of("code", 200, "message", "删除数据源成功"));
    }

    @PostMapping("/test")
    public ResponseEntity<Map<String, Object>> testDataSource(@Valid @RequestBody DataSourceRequest requestBody) {
        String username = securityAuditConfig.getCurrentUsername();
        Map<String, Object> result = dataSourceService.testDataSource(toMap(requestBody));
        securityAuditConfig.logUserActivity(username, "测试数据源", "成功测试数据源: " + requestBody.getType());
        return ResponseEntity.ok(Map.of("code", 200, "message", "测试数据源成功", "data", result));
    }

    @GetMapping("/types")
    public ResponseEntity<Map<String, Object>> getDataSourceTypes() {
        String username = securityAuditConfig.getCurrentUsername();
        List<Map<String, Object>> types = dataSourceService.getDataSourceTypes();
        securityAuditConfig.logUserActivity(username, "获取数据源类型", "成功获取数据源类型列表");
        return ResponseEntity.ok(Map.of("code", 200, "message", "获取数据源类型成功", "data", types));
    }

    private Map<String, Object> toMap(DataSourceRequest dto) {
        Map<String, Object> map = new java.util.LinkedHashMap<>();
        map.put("name", dto.getName());
        map.put("type", dto.getType());
        map.put("format", dto.getFormat());
        map.put("config", dto.getConfig());
        map.put("description", dto.getDescription());
        return map;
    }
}

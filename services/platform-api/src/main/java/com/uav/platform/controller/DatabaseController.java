package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

/**
 * 数据库管理控制器
 * <p>
 * 提供数据库列表、表结构查询、SQL 执行等功能，仅限 SUPER_ADMIN 角色使用。
 */
@RestController
@RequestMapping("/api/v1/database")
@RequiredArgsConstructor
public class DatabaseController {

    private final DataSource dataSource;

    private final JdbcTemplate jdbcTemplate;

    /**
     * 获取数据库列表
     */
    @GetMapping("/list")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<List<Map<String, Object>>> getDatabases() {
        List<Map<String, Object>> databases = jdbcTemplate.queryForList(
                "SELECT SCHEMA_NAME AS name, " +
                "ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS sizeMb, " +
                "COUNT(TABLE_NAME) AS tableCount " +
                "FROM information_schema.SCHEMATA s " +
                "LEFT JOIN information_schema.TABLES t ON s.SCHEMA_NAME = t.TABLE_SCHEMA " +
                "WHERE s.SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys') " +
                "GROUP BY SCHEMA_NAME"
        );
        return Result.success(databases);
    }

    /**
     * 获取指定数据库下的表列表
     */
    @GetMapping("/tables")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<List<Map<String, Object>>> getTables(@RequestParam(defaultValue = "uav_platform") String database) {
        List<Map<String, Object>> tables = jdbcTemplate.queryForList(
                "SELECT TABLE_NAME AS name, TABLE_COMMENT AS comment, TABLE_ROWS AS rows, " +
                "COUNT(COLUMN_NAME) AS columns, ENGINE AS engine, CREATE_TIME AS createTime " +
                "FROM information_schema.TABLES t " +
                "LEFT JOIN information_schema.COLUMNS c ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME " +
                "WHERE TABLE_SCHEMA = ? " +
                "GROUP BY TABLE_NAME", database);
        return Result.success(tables);
    }

    /**
     * 获取指定表的列信息
     */
    @GetMapping("/tables/columns")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<List<Map<String, Object>>> getColumns(
            @RequestParam String database, @RequestParam String table) {
        List<Map<String, Object>> columns = jdbcTemplate.queryForList(
                "SELECT COLUMN_NAME AS name, COLUMN_TYPE AS type, IS_NULLABLE AS nullable, " +
                "COLUMN_KEY AS `key`, COLUMN_DEFAULT AS `default`, COLUMN_COMMENT AS comment " +
                "FROM information_schema.COLUMNS " +
                "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
                database, table);
        return Result.success(columns);
    }

    /**
     * 获取指定表的数据（分页）
     */
    @GetMapping("/tables/data")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Map<String, Object>> getTableData(
            @RequestParam String database, @RequestParam String table,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        int offset = (page - 1) * size;
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT * FROM `" + database + "`.`" + table + "` LIMIT ? OFFSET ?", size, offset);
        Long total = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM `" + database + "`.`" + table + "`", Long.class);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("rows", rows);
        result.put("total", total);
        result.put("page", page);
        result.put("size", size);
        return Result.success(result);
    }

    /**
     * 执行 SQL 查询/更新
     * <p>
     * 安全限制：禁止 DROP DATABASE / DROP SCHEMA 操作，查询结果最多返回 500 行。
     */
    @PostMapping("/query")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Map<String, Object>> executeQuery(@RequestBody Map<String, String> body) {
        String sql = body.get("sql");
        if (sql == null || sql.trim().isEmpty()) {
            return Result.error(400, "SQL 不能为空");
        }

        // 安全检查：禁止 DROP DATABASE, TRUNCATE 等危险操作
        String upperSql = sql.trim().toUpperCase();
        if (upperSql.startsWith("DROP DATABASE") || upperSql.startsWith("DROP SCHEMA")) {
            return Result.error(403, "禁止执行 DROP DATABASE 操作");
        }

        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {

            boolean isQuery = upperSql.startsWith("SELECT")
                    || upperSql.startsWith("SHOW")
                    || upperSql.startsWith("DESCRIBE")
                    || upperSql.startsWith("EXPLAIN");

            if (isQuery) {
                ResultSet rs = stmt.executeQuery(sql);
                ResultSetMetaData meta = rs.getMetaData();
                int colCount = meta.getColumnCount();

                List<String> columns = new ArrayList<>();
                for (int i = 1; i <= colCount; i++) {
                    columns.add(meta.getColumnLabel(i));
                }

                List<Map<String, Object>> rows = new ArrayList<>();
                int limit = 500;
                while (rs.next() && rows.size() < limit) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    for (int i = 1; i <= colCount; i++) {
                        row.put(columns.get(i - 1), rs.getObject(i));
                    }
                    rows.add(row);
                }

                Map<String, Object> result = new LinkedHashMap<>();
                result.put("columns", columns);
                result.put("rows", rows);
                result.put("total", rows.size());
                return Result.success(result);
            } else {
                int affected = stmt.executeUpdate(sql);
                Map<String, Object> result = new LinkedHashMap<>();
                result.put("affectedRows", affected);
                result.put("message", "执行成功，影响 " + affected + " 行");
                return Result.success(result);
            }
        } catch (Exception e) {
            return Result.error(500, "SQL 执行错误: " + e.getMessage());
        }
    }
}

package com.uav.common.config;

import java.util.Set;

/**
 * 统一脚本白名单管理
 *
 * 集中管理系统中允许执行的Python脚本和操作列表，
 * 避免在各个服务中重复定义导致的不一致问题。
 *
 * 使用方式：
 * <pre>{@code
 * // 验证脚本名
 * ScriptWhitelistConfig.validateScript("wrf_processor.py");
 *
 * // 验证操作名
 * ScriptWhitelistConfig.validateAction("predict");
 *
 * // 获取白名单
 * Set<String> scripts = ScriptWhitelistConfig.getAllowedScripts();
 * }</pre>
 */
public final class ScriptWhitelistConfig {

    private ScriptWhitelistConfig() {
    }

    /** 允许执行的脚本白名单 */
    private static final Set<String> ALLOWED_SCRIPTS = Set.of(
        // WRF 处理脚本
        "wrf_processor.py",
        "wrf_parser.py",
        "wrf_converter.py",
        // 气象预测脚本
        "meteor_forecast.py",
        "prediction/meteor_forecast.py",
        // 路径规划脚本
        "path_planner.py",
        "three_layer_planner.py",
        "advanced_planners.py",
        "path-planning/three_layer_planner.py",
        "vrp/optimize_routes.py",
        // 数据同化脚本
        "assimilation.py",
        "data_assimilation.py",
        "reinforcement_learning.py",
        "assimilation/bayesian_assimilation.py"
    );

    /** 允许执行的操作白名单 */
    private static final Set<String> ALLOWED_ACTIONS = Set.of(
        // 通用操作
        "predict", "plan", "compute", "assimilate", "optimize",
        "parse", "validate", "transform", "execute", "batch",
        // 路径规划操作
        "vrptw", "astar", "dwa", "full",
        "global_path", "local_avoidance",
        // 数据操作
        "variance", "correct",
        // 气象操作
        "get_forecast", "get_detailed_forecast", "get_realtime_weather"
    );

    /**
     * 获取允许执行的脚本白名单（不可修改）
     */
    public static Set<String> getAllowedScripts() {
        return ALLOWED_SCRIPTS;
    }

    /**
     * 获取允许执行的操作白名单（不可修改）
     */
    public static Set<String> getAllowedActions() {
        return ALLOWED_ACTIONS;
    }

    /**
     * 验证脚本名称是否在白名单中
     *
     * @param scriptName 脚本文件名
     * @throws SecurityException 如果脚本不在白名单中
     */
    public static void validateScript(String scriptName) {
        if (scriptName == null || scriptName.trim().isEmpty()) {
            throw new SecurityException("脚本名称不能为空");
        }
        if (scriptName.contains("..") || scriptName.contains("\\")) {
            throw new SecurityException("非法的脚本名称: 检测到路径遍历");
        }
        if (!ALLOWED_SCRIPTS.contains(scriptName)) {
            throw new SecurityException("脚本不在白名单中: " + scriptName);
        }
    }

    /**
     * 验证操作名称是否在白名单中
     *
     * @param action 操作名称
     * @throws SecurityException 如果操作不在白名单中
     */
    public static void validateAction(String action) {
        if (action == null || action.trim().isEmpty()) {
            throw new SecurityException("操作名称不能为空");
        }
        if (!ALLOWED_ACTIONS.contains(action)) {
            throw new SecurityException("操作不在白名单中: " + action);
        }
    }
}

package com.uav.common.integration;

import org.junit.platform.suite.api.SelectClasses;
import org.junit.platform.suite.api.Suite;
import org.junit.platform.suite.api.SuiteDisplayName;

/**
 * 集成测试套件
 * 
 * 按顺序运行所有集成测试：
 * 1. 认证流程 (AuthFlowIntegrationTest)
 * 2. 路径规划 (PathPlanningIntegrationTest)
 * 
 * 运行方式：
 *   mvn test -Dtest="com.uav.common.integration.IntegrationTestSuite" \
 *            -Dtest.target=http://localhost:8089 \
 *            -Dtest.planning=http://localhost:8083
 */
@Suite
@SelectClasses({
    AuthFlowIntegrationTest.class,
    PathPlanningIntegrationTest.class
})
@SuiteDisplayName("全系统集成测试套件")
public class IntegrationTestSuite {
}

#!/usr/bin/env python3
"""
基础功能测试
不依赖外部库，只测试基本功能
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestBasic(unittest.TestCase):
    """
    基础测试类
    """
    
    def test_system_structure(self):
        """
        测试系统结构是否完整
        """
        print("测试系统结构...")
        
        # 检查主要目录是否存在
        self.assertTrue(os.path.exists('uav-path-planning-system'))
        self.assertTrue(os.path.exists('wrf-processor-service'))
        self.assertTrue(os.path.exists('meteor-forecast-service'))
        self.assertTrue(os.path.exists('path-planning-service'))
        self.assertTrue(os.path.exists('uav-platform-service'))
        self.assertTrue(os.path.exists('data-assimilation-platform'))
        self.assertTrue(os.path.exists('data-assimilation-service'))
        
        # 检查配置文件是否存在
        self.assertTrue(os.path.exists('docker-compose.yml'))
        
        print("OK 系统结构测试通过")
    
    def test_frontend_files(self):
        """
        测试前端文件是否存在
        """
        print("测试前端文件...")
        
        frontend_path = 'uav-path-planning-system/frontend-vue'
        self.assertTrue(os.path.exists(f'{frontend_path}/package.json'))
        self.assertTrue(os.path.exists(f'{frontend_path}/src/App.vue'))
        self.assertTrue(os.path.exists(f'{frontend_path}/src/views/PathPlanningView.vue'))
        self.assertTrue(os.path.exists(f'{frontend_path}/src/views/WeatherView.vue'))
        self.assertTrue(os.path.exists(f'{frontend_path}/src/views/MonitoringView.vue'))
        self.assertTrue(os.path.exists(f'{frontend_path}/src/views/HistoryView.vue'))
        
        # 检查工具类文件
        self.assertTrue(os.path.exists(f'{frontend_path}/src/utils/performance.js'))
        self.assertTrue(os.path.exists(f'{frontend_path}/src/utils/errorHandler.js'))
        self.assertTrue(os.path.exists(f'{frontend_path}/src/utils/visualization.js'))
        
        print("OK 前端文件测试通过")
    
    def test_backend_files(self):
        """
        测试后端文件是否存在
        """
        print("测试后端文件...")
        
        backend_path = 'uav-path-planning-system/backend-spring'
        self.assertTrue(os.path.exists(f'{backend_path}/src/main/java/com/uav/config/SecurityConfig.java'))
        self.assertTrue(os.path.exists(f'{backend_path}/src/main/java/com/uav/config/JwtUtil.java'))
        self.assertTrue(os.path.exists(f'{backend_path}/src/main/java/com/uav/config/JwtFilter.java'))
        self.assertTrue(os.path.exists(f'{backend_path}/src/main/java/com/uav/model/User.java'))
        self.assertTrue(os.path.exists(f'{backend_path}/src/main/java/com/uav/model/Role.java'))
        self.assertTrue(os.path.exists(f'{backend_path}/src/main/java/com/uav/service/CustomUserDetailsService.java'))
        
        print("OK 后端文件测试通过")
    
    def test_algorithm_files(self):
        """
        测试算法文件是否存在
        """
        print("测试算法文件...")
        
        # 检查贝叶斯同化算法
        assimilation_path = 'data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models'
        self.assertTrue(os.path.exists(f'{assimilation_path}/base.py'))
        self.assertTrue(os.path.exists(f'{assimilation_path}/three_dimensional_var.py'))
        self.assertTrue(os.path.exists(f'{assimilation_path}/four_dimensional_var.py'))
        self.assertTrue(os.path.exists(f'{assimilation_path}/enkf.py'))
        self.assertTrue(os.path.exists(f'{assimilation_path}/hybrid.py'))
        
        # 检查路径规划算法
        planning_path = 'path-planning-service/src/main/python'
        self.assertTrue(os.path.exists(f'{planning_path}/three_layer_planner.py'))
        self.assertTrue(os.path.exists(f'{planning_path}/advanced_planners.py'))
        self.assertTrue(os.path.exists(f'{planning_path}/reinforcement_learning.py'))
        self.assertTrue(os.path.exists(f'{planning_path}/multi_objective_planner.py'))
        self.assertTrue(os.path.exists(f'{planning_path}/uncertainty_planner.py'))
        self.assertTrue(os.path.exists(f'{planning_path}/digital_twin.py'))
        self.assertTrue(os.path.exists(f'{planning_path}/knowledge_graph.py'))
        
        # 检查气象预测算法
        meteor_path = 'meteor-forecast-service/src/main/python'
        self.assertTrue(os.path.exists(f'{meteor_path}/meteor_forecast.py'))
        
        # 检查端侧SDK
        edge_path = 'uav-edge-sdk/src'
        self.assertTrue(os.path.exists(f'{edge_path}/edge_sdk.py'))
        
        print("OK 算法文件测试通过")
    
    def test_deployment_files(self):
        """
        测试部署文件是否存在
        """
        print("测试部署文件...")
        
        # 检查Kubernetes配置
        k8s_path = 'deployments/kubernetes'
        self.assertTrue(os.path.exists(f'{k8s_path}/namespace.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/persistent-volumes.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/database-services.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/frontend-vue.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/path-planning-service.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/uav-platform-service.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/autoscaling.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/monitoring.yml'))
        self.assertTrue(os.path.exists(f'{k8s_path}/deploy.sh'))
        
        # 检查数据库优化脚本
        db_path = 'deployments/database'
        self.assertTrue(os.path.exists(f'{db_path}/optimize.sql'))
        
        print("OK 部署文件测试通过")

if __name__ == '__main__':
    unittest.main()

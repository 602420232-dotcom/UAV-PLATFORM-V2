#!/usr/bin/env python3
"""
气象预测与订正服务
使用LSTM+XGBoost+ConvLSTM+GPR模型进行气象预测与订正
"""

import numpy as np
import pandas as pd
import json
import sys
import os
import logging
import threading
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, ConvLSTM2D, BatchNormalization, Flatten, Reshape
from xgboost import XGBRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel, ConstantKernel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 缓存机制
class Cache:
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = {}
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            return self.cache.get(key)
    
    def set(self, key, value):
        with self.lock:
            if len(self.cache) >= self.max_size:
                # 移除最早的项
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = value

# 全局缓存实例
prediction_cache = Cache()
fusion_cache = Cache()
risk_cache = Cache()

class MeteorForecast:
    """
    气象预测与订正模型
    """
    
    def __init__(self, model_path=None):
        """
        初始化气象预测模型
        :param model_path: 模型保存路径
        """
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_path, exist_ok=True)
        self.lstm_model = None
        self.xgb_model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.history = []  # 训练历史
        self.best_score = float('inf')  # 最佳模型分数
        self.wrf_data = None  # WRF数据
        self.ghr_data = None  # 风乌GHR数据
        # 预加载模型
        self.load_models()
    
    def prepare_data(self, data, look_back=24):
        """
        准备时间序列数据
        :param data: 输入数据
        :param look_back: 回溯窗口大小
        :return: 特征和标签
        """
        X, y = [], []
        for i in range(len(data) - look_back):
            X.append(data[i:(i + look_back)])
            y.append(data[i + look_back])
        return np.array(X), np.array(y)
    
    def train_lstm(self, X, y, epochs=50, batch_size=32):
        """
        训练LSTM模型
        :param X: 特征数据
        :param y: 标签数据
        :param epochs: 训练轮数
        :param batch_size: 批次大小
        """
        try:
            # 构建LSTM模型
            self.lstm_model = Sequential()
            self.lstm_model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
            self.lstm_model.add(Dropout(0.2))
            self.lstm_model.add(LSTM(50, return_sequences=False))
            self.lstm_model.add(Dropout(0.2))
            self.lstm_model.add(Dense(25))
            self.lstm_model.add(Dense(1))
            
            # 编译模型
            self.lstm_model.compile(optimizer='adam', loss='mean_squared_error')
            
            # 训练模型
            self.lstm_model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=1)
            
            # 保存模型
            lstm_model_path = os.path.join(self.model_path, 'lstm_model.h5')
            self.lstm_model.save(lstm_model_path)
            logger.info(f"LSTM模型保存成功: {lstm_model_path}")
            
        except Exception as e:
            logger.error(f"训练LSTM模型失败: {e}")
    
    def train_xgb(self, X, y):
        """
        训练XGBoost模型
        :param X: 特征数据
        :param y: 标签数据
        """
        try:
            # 构建XGBoost模型
            self.xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, n_jobs=-1)
            
            # 训练模型
            self.xgb_model.fit(X, y)
            
            # 保存模型
            xgb_model_path = os.path.join(self.model_path, 'xgb_model.json')
            self.xgb_model.save_model(xgb_model_path)
            logger.info(f"XGBoost模型保存成功: {xgb_model_path}")
            
        except Exception as e:
            logger.error(f"训练XGBoost模型失败: {e}")
    
    def load_models(self):
        """
        加载保存的模型
        """
        try:
            # 加载LSTM模型
            lstm_model_path = os.path.join(self.model_path, 'lstm_model.h5')
            if os.path.exists(lstm_model_path):
                self.lstm_model = load_model(lstm_model_path)
                logger.info(f"LSTM模型加载成功: {lstm_model_path}")
            else:
                logger.warning(f"LSTM模型文件不存在: {lstm_model_path}")
            
            # 加载XGBoost模型
            xgb_model_path = os.path.join(self.model_path, 'xgb_model.json')
            if os.path.exists(xgb_model_path):
                self.xgb_model = XGBRegressor(n_jobs=-1)
                self.xgb_model.load_model(xgb_model_path)
                logger.info(f"XGBoost模型加载成功: {xgb_model_path}")
            else:
                logger.warning(f"XGBoost模型文件不存在: {xgb_model_path}")
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
    
    def predict(self, input_data):
        """
        执行气象预测
        :param input_data: 输入数据
        :return: 预测结果
        """
        try:
            # 生成缓存键
            cache_key = str(input_data)
            # 检查缓存
            cached_result = prediction_cache.get(cache_key)
            if cached_result:
                logger.info("使用缓存的预测结果")
                return cached_result
            
            # 数据预处理
            scaled_data = self.scaler.transform(np.array(input_data).reshape(-1, 1))
            X, _ = self.prepare_data(scaled_data, look_back=24)
            
            # 检查模型是否存在
            if self.lstm_model is None or self.xgb_model is None:
                logger.warning("模型未初始化，无法进行预测")
                return []
            
            # LSTM预测
            lstm_pred = self.lstm_model.predict(X, batch_size=32)
            
            # XGBoost预测（使用LSTM的预测结果作为特征）
            xgb_pred = self.xgb_model.predict(lstm_pred)
            
            # 反归一化
            predictions = self.scaler.inverse_transform(xgb_pred.reshape(-1, 1))
            result = predictions.tolist()
            
            # 缓存结果
            prediction_cache.set(cache_key, result)
            
            logger.info("气象预测完成")
            return result
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return []
    
    def correct(self, forecast_data, observed_data):
        """
        执行气象数据订正
        :param forecast_data: 预测数据
        :param observed_data: 观测数据
        :return: 订正结果
        """
        try:
            # 计算预测误差
            error = np.array(observed_data) - np.array(forecast_data)
            
            # 准备特征数据（使用预测值作为特征）
            X = np.array(forecast_data).reshape(-1, 1)
            
            # 预测误差
            error_pred = self.xgb_model.predict(X)
            
            # 应用订正值
            corrected_data = np.array(forecast_data) + error_pred
            
            logger.info("气象数据订正完成")
            return corrected_data.tolist()
            
        except Exception as e:
            logger.error(f"订正失败: {e}")
            return forecast_data
    
    def evaluate(self, X, y):
        """
        评估模型性能
        :param X: 特征数据
        :param y: 标签数据
        :return: 评估结果
        """
        try:
            # 检查模型是否存在
            if self.lstm_model is None or self.xgb_model is None:
                logger.warning("模型未初始化，无法进行评估")
                return {}
            
            # LSTM预测
            lstm_pred = self.lstm_model.predict(X, batch_size=32)
            
            # XGBoost预测
            xgb_pred = self.xgb_model.predict(lstm_pred)
            
            # 计算MSE
            mse = mean_squared_error(y, xgb_pred)
            rmse = np.sqrt(mse)
            
            logger.info(f"模型评估完成，RMSE: {rmse}")
            return {
                'mse': float(mse),
                'rmse': float(rmse)
            }
            
        except Exception as e:
            logger.error(f"评估失败: {e}")
            return {}
    
    def self_improve(self, new_data, epochs=20, batch_size=32):
        """
        自迭代改进模型
        :param new_data: 新的训练数据
        :param epochs: 训练轮数
        :param batch_size: 批次大小
        :return: 改进结果
        """
        try:
            logger.info("开始自迭代改进模型...")
            
            # 准备数据
            scaled_data = self.scaler.transform(np.array(new_data).reshape(-1, 1))
            X, y = self.prepare_data(scaled_data, look_back=24)
            
            # 检查模型是否存在，如果不存在则创建新模型
            if self.lstm_model is None:
                logger.info("LSTM模型未初始化，创建新模型")
                self.lstm_model = Sequential()
                self.lstm_model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
                self.lstm_model.add(Dropout(0.2))
                self.lstm_model.add(LSTM(50, return_sequences=False))
                self.lstm_model.add(Dropout(0.2))
                self.lstm_model.add(Dense(25))
                self.lstm_model.add(Dense(1))
                self.lstm_model.compile(optimizer='adam', loss='mean_squared_error')
            
            if self.xgb_model is None:
                logger.info("XGBoost模型未初始化，创建新模型")
                self.xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, n_jobs=-1)
            
            # 继续训练LSTM模型
            history = self.lstm_model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=1, validation_split=0.2)
            
            # 训练XGBoost模型
            self.xgb_model.fit(X.reshape(X.shape[0], -1), y)
            
            # 评估模型
            eval_result = self.evaluate(X, y)
            current_score = eval_result.get('rmse', float('inf'))
            
            # 保存训练历史
            self.history.append({
                'timestamp': pd.Timestamp.now().isoformat(),
                'rmse': current_score,
                'epochs': epochs
            })
            
            # 保存最佳模型
            if current_score < self.best_score and self.lstm_model is not None and self.xgb_model is not None:
                self.best_score = current_score
                lstm_model_path = os.path.join(self.model_path, 'lstm_model.h5')
                xgb_model_path = os.path.join(self.model_path, 'xgb_model.json')
                self.lstm_model.save(lstm_model_path)
                self.xgb_model.save_model(xgb_model_path)
                logger.info(f"最佳模型已更新，RMSE: {current_score}")
                # 清空缓存，确保使用新模型
                prediction_cache.cache.clear()
                fusion_cache.cache.clear()
            
            logger.info("模型自迭代改进完成")
            return {
                'success': True,
                'rmse': current_score,
                'best_rmse': self.best_score
            }
            
        except Exception as e:
            logger.error(f"自迭代改进失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def load_wrf_data(self, wrf_data):
        """
        加载WRF数据
        :param wrf_data: WRF数据
        """
        try:
            self.wrf_data = wrf_data
            logger.info("WRF数据加载成功")
            return True
        except Exception as e:
            logger.error(f"加载WRF数据失败: {e}")
            return False
    
    def load_ghr_data(self, ghr_data):
        """
        加载风乌GHR数据
        :param ghr_data: 风乌GHR数据
        """
        try:
            self.ghr_data = ghr_data
            logger.info("风乌GHR数据加载成功")
            return True
        except Exception as e:
            logger.error(f"加载风乌GHR数据失败: {e}")
            return False

    def build_convlstm_model(self, input_shape):
        """构建ConvLSTM时空预测模型"""
        model = Sequential([
            ConvLSTM2D(filters=32, kernel_size=(3, 3), padding='same', return_sequences=True, input_shape=input_shape),
            BatchNormalization(),
            ConvLSTM2D(filters=16, kernel_size=(3, 3), padding='same', return_sequences=False),
            BatchNormalization(),
            Flatten(),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        logger.info(f"ConvLSTM模型构建完成, 输入形状: {input_shape}")
        return model

    def convlstm_predict(self, spatial_series):
        """使用ConvLSTM进行时空序列预测"""
        try:
            if not hasattr(self, 'convlstm_model') or self.convlstm_model is None:
                logger.info("ConvLSTM模型未初始化，构建默认模型")
                input_shape = (spatial_series.shape[0], spatial_series.shape[1], spatial_series.shape[2], 1)
                self.convlstm_model = self.build_convlstm_model(input_shape[1:])
            return self.convlstm_model.predict(spatial_series, verbose=0)
        except Exception as e:
            logger.error(f"ConvLSTM预测失败: {e}")
            return None

    def train_gpr(self, X_train, y_train):
        """训练高斯过程回归模型"""
        try:
            kernel = ConstantKernel(1.0) * RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
            self.gpr_model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, alpha=1e-6)
            self.gpr_model.fit(X_train, y_train)
            logger.info("GPR模型训练完成")
            return True
        except Exception as e:
            logger.error(f"GPR模型训练失败: {e}")
            return False

    def gpr_predict(self, X_test, return_std=True):
        """使用高斯过程回归进行预测，返回预测值和不确定性"""
        try:
            if not hasattr(self, 'gpr_model') or self.gpr_model is None:
                logger.warning("GPR模型未训练")
                return None, None
            if return_std:
                return self.gpr_model.predict(X_test, return_std=True)
            return self.gpr_model.predict(X_test), None
        except Exception as e:
            logger.error(f"GPR预测失败: {e}")
            return None, None

    def fusion_forecast(self, input_data):
        """
        双预报引擎融合预测
        :param input_data: 输入数据
        :return: 融合预测结果
        """
        try:
            # 生成缓存键
            cache_key = str(input_data) + str(self.wrf_data) + str(self.ghr_data)
            # 检查缓存
            cached_result = fusion_cache.get(cache_key)
            if cached_result:
                logger.info("使用缓存的融合预测结果")
                return cached_result
            
            # 数据预处理
            scaled_data = self.scaler.transform(np.array(input_data).reshape(-1, 1))
            X, _ = self.prepare_data(scaled_data, look_back=24)
            
            # 检查模型是否存在
            if self.lstm_model is None or self.xgb_model is None:
                logger.warning("模型未初始化，无法进行融合预测")
                return []
            
            # LSTM预测
            lstm_pred = self.lstm_model.predict(X, batch_size=32)
            
            # XGBoost预测（使用LSTM的预测结果作为特征）
            xgb_pred = self.xgb_model.predict(lstm_pred)
            
            # 反归一化
            predictions = self.scaler.inverse_transform(xgb_pred.reshape(-1, 1))
            
            # 如果有WRF和GHR数据，进行融合
            if self.wrf_data and self.ghr_data:
                # 这里实现简单的加权融合，实际应用中可以使用更复杂的融合策略
                wrf_pred = np.array(self.wrf_data.get('predictions', []))
                ghr_pred = np.array(self.ghr_data.get('predictions', []))
                
                if len(wrf_pred) > 0 and len(ghr_pred) > 0:
                    # 加权融合
                    weights = [0.4, 0.3, 0.3]  # LSTM+XGBoost, WRF, GHR的权重
                    fused_predictions = (predictions * weights[0] + 
                                        wrf_pred[:len(predictions)] * weights[1] + 
                                        ghr_pred[:len(predictions)] * weights[2])
                    predictions = fused_predictions
            
            result = predictions.tolist()
            # 缓存结果
            fusion_cache.set(cache_key, result)
            
            logger.info("双预报引擎融合预测完成")
            return result
            
        except Exception as e:
            logger.error(f"融合预测失败: {e}")
            return []
    
    def generate_risk_heatmap(self, forecast_data):
        """
        生成风险热力图
        :param forecast_data: 预测数据
        :return: 风险热力图数据
        """
        try:
            # 生成缓存键
            cache_key = str(forecast_data)
            # 检查缓存
            cached_result = risk_cache.get(cache_key)
            if cached_result:
                logger.info("使用缓存的风险热力图结果")
                return cached_result
            
            # 这里实现简单的风险热力图生成，实际应用中可以使用更复杂的算法
            risk_data = []
            for i, value in enumerate(forecast_data):
                # 基于预测值计算风险等级
                if value > 20:
                    risk_level = 5  # 高风险
                elif value > 15:
                    risk_level = 4
                elif value > 10:
                    risk_level = 3
                elif value > 5:
                    risk_level = 2
                else:
                    risk_level = 1  # 低风险
                risk_data.append({
                    'index': i,
                    'value': value,
                    'risk_level': risk_level
                })
            
            # 缓存结果
            risk_cache.set(cache_key, risk_data)
            
            logger.info("风险热力图生成完成")
            return risk_data
            
        except Exception as e:
            logger.error(f"生成风险热力图失败: {e}")
            return []

def load_input(file_index):
    """从文件加载JSON输入数据，防止命令注入"""
    if len(sys.argv) <= file_index:
        return {}
    file_path = sys.argv[file_index]
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        logger.error("缺少命令参数")
        print(json.dumps({
            'success': False,
            'error': '缺少命令参数'
        }))
        return
    
    command = sys.argv[1]
    model = MeteorForecast()
    
    if command == 'predict':
        # 预测命令
        if len(sys.argv) < 3:
            logger.error("缺少输入数据")
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            predictions = model.predict(input_data)
            logger.info("预测完成")
            print(json.dumps({
                'success': True,
                'data': predictions
            }))
        except Exception as e:
            logger.error(f"预测失败: {e}")
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'correct':
        # 订正命令
        if len(sys.argv) < 4:
            logger.error("缺少预测数据和观测数据")
            print(json.dumps({
                'success': False,
                'error': '缺少预测数据和观测数据'
            }))
            return
        
        try:
            forecast_data = load_input(2)
            observed_data = load_input(3)
            corrected_data = model.correct(forecast_data, observed_data)
            print(json.dumps({
                'success': True,
                'data': corrected_data
            }))
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'train':
        # 训练命令
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少训练数据'
            }))
            return
        
        try:
            training_data = load_input(2)
            # 准备数据
            scaled_data = model.scaler.fit_transform(np.array(training_data).reshape(-1, 1))
            X, y = model.prepare_data(scaled_data, look_back=24)
            # 训练模型
            model.train_lstm(X, y)
            model.train_xgb(X.reshape(X.shape[0], -1), y)
            print(json.dumps({
                'success': True,
                'message': '模型训练完成'
            }))
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'improve':
        # 自迭代改进命令
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少改进数据'
            }))
            return
        
        try:
            improve_data = load_input(2)
            new_data = improve_data.get('data', [])
            epochs = improve_data.get('epochs', 20)
            batch_size = improve_data.get('batch_size', 32)
            # 执行自迭代改进
            result = model.self_improve(new_data, epochs, batch_size)
            print(json.dumps({
                'success': result['success'],
                'data': result
            }))
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'fusion':
        # 双预报引擎融合预测命令
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            forecast_data = input_data.get('forecast_data', [])
            wrf_data = input_data.get('wrf_data', {})
            ghr_data = input_data.get('ghr_data', {})
            
            # 加载数据
            model.load_wrf_data(wrf_data)
            model.load_ghr_data(ghr_data)
            
            # 执行融合预测
            predictions = model.fusion_forecast(forecast_data)
            print(json.dumps({
                'success': True,
                'data': predictions
            }))
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'risk':
        # 生成风险热力图命令
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少预测数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            forecast_data = input_data.get('forecast_data', [])
            
            # 生成风险热力图
            risk_data = model.generate_risk_heatmap(forecast_data)
            print(json.dumps({
                'success': True,
                'data': risk_data
            }))
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    else:
        print(json.dumps({
            'success': False,
            'error': '未知命令'
        }))

if __name__ == "__main__":
    main()
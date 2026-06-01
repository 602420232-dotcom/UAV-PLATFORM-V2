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
import pickle
from datetime import datetime
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, ConvLSTM2D, BatchNormalization, Flatten, Reshape
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from xgboost import XGBRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel, ConstantKernel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 缓存机制
from common_utils.cache import Cache

# 全局缓存实例
prediction_cache = Cache()
fusion_cache = Cache()
risk_cache = Cache()

class MeteorForecast:
    """
    气象预测与订正模型
    """
    
    def __init__(self, model_path=None):
        """Initialize the meteor forecast model.

        Args:
            model_path: Path to the model directory.
        """
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_path, exist_ok=True)
        self.lstm_model = None
        self.xgb_model = None
        self.gpr_model = None
        self.convlstm_model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.history = []  # 训练历史
        self.best_score = float('inf')  # 最佳模型分数
        self.wrf_data = None  # WRF数据
        self.ghr_data = None  # 风乌GHR数据
        self.model_metadata = self._load_model_metadata()
        self.current_model_version = model_version or self.model_metadata.get('version', 'latest')
        self.load_models(model_version)

    def prepare_data(self, data, look_back=24):
        """Prepare time series data with sliding window.

        Args:
            data: Input time series data.
            look_back: Window size for historical steps.

        Returns:
            Tuple of (X features, y labels).
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
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"训练XGBoost模型失败: {e}")
    
    def _load_model_metadata(self):
        """加载模型元数据"""
        metadata_path = os.path.join(self.model_path, 'model_metadata.json')
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载模型元数据失败: {e}")
        return {
            'models': {},
            'last_trained': None,
            'version': '1.0.0'
        }
    
    def _save_model_metadata(self):
        """保存模型元数据"""
        metadata_path = os.path.join(self.model_path, 'model_metadata.json')
        self.model_metadata['last_updated'] = datetime.now().isoformat()
        try:
            with open(metadata_path, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"保存模型元数据失败: {e}")
    
    def load_models(self, model_version=None):
        """
        加载保存的模型

        :param model_version: 可选的模型版本
        :return: True-全部加载成功, False-部分或全部加载失败
        """
        successful_models = 0
        total_models = 4  # lstm, xgb, gpr, scaler

        try:
            # 加载LSTM模型
            lstm_filename = f'lstm_model_{model_version}.h5' if model_version else 'lstm_model.h5'
            lstm_model_path = os.path.join(self.model_path, lstm_filename)
            if os.path.exists(lstm_model_path):
                self.lstm_model = load_model(lstm_model_path)
                logger.info(f"LSTM模型加载成功: {lstm_model_path}")
                successful_models += 1
            else:
                logger.warning(f"LSTM模型文件不存在: {lstm_model_path}")
                self.lstm_model = None

            # 加载XGBoost模型
            xgb_filename = f'xgb_model_{model_version}.json' if model_version else 'xgb_model.json'
            xgb_model_path = os.path.join(self.model_path, xgb_filename)
            if os.path.exists(xgb_model_path):
                self.xgb_model = XGBRegressor(n_jobs=-1)
                self.xgb_model.load_model(xgb_model_path)
                logger.info(f"XGBoost模型加载成功: {xgb_model_path}")
                successful_models += 1
            else:
                logger.warning(f"XGBoost模型文件不存在: {xgb_model_path}")
                self.xgb_model = None

            # 加载GPR模型
            gpr_filename = f'gpr_model_{model_version}.pkl' if model_version else 'gpr_model.pkl'
            gpr_model_path = os.path.join(self.model_path, gpr_filename)
            if os.path.exists(gpr_model_path):
                with open(gpr_model_path, 'rb') as f:
                    self.gpr_model = pickle.load(f)
                logger.info(f"GPR模型加载成功: {gpr_model_path}")
                successful_models += 1
            else:
                logger.warning(f"GPR模型文件不存在: {gpr_model_path}")
                self.gpr_model = None

            # 加载scaler
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info(f"Scaler加载成功: {scaler_path}")
                successful_models += 1

            # 加载训练历史
            history_path = os.path.join(self.model_path, 'training_history.json')
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    self.history = json.load(f)
                logger.info(f"训练历史加载成功: {history_path}")

        except Exception as e:
            logger.error(f"模型加载失败 (version={model_version}): {e}", exc_info=True)
            return False

        if successful_models == total_models:
            logger.info(f"所有模型加载成功 (version={model_version})")
            return True
        else:
            logger.warning(f"部分模型加载成功: {successful_models}/{total_models} (version={model_version})")
            return False
    
    def save_models(self, version=None):
        """
        保存模型到文件
        :param version: 可选的版本号
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            version_suffix = f'_{version}' if version else ''
            version = version or 'latest'

            # 保存LSTM模型
            if self.lstm_model:
                lstm_path = os.path.join(self.model_path, f'lstm_model{version_suffix}.h5')
                self.lstm_model.save(lstm_path)
                logger.info(f"LSTM模型保存成功: {lstm_path}")
                self.model_metadata['models']['lstm'] = {
                    'path': lstm_path,
                    'version': version,
                    'timestamp': timestamp
                }

            # 保存XGBoost模型
            if self.xgb_model:
                xgb_path = os.path.join(self.model_path, f'xgb_model{version_suffix}.json')
                self.xgb_model.save_model(xgb_path)
                logger.info(f"XGBoost模型保存成功: {xgb_path}")
                self.model_metadata['models']['xgb'] = {
                    'path': xgb_path,
                    'version': version,
                    'timestamp': timestamp
                }

            # 保存GPR模型
            if self.gpr_model:
                gpr_path = os.path.join(self.model_path, f'gpr_model{version_suffix}.pkl')
                with open(gpr_path, 'wb') as f:
                    pickle.dump(self.gpr_model, f)
                logger.info(f"GPR模型保存成功: {gpr_path}")
                self.model_metadata['models']['gpr'] = {
                    'path': gpr_path,
                    'version': version,
                    'timestamp': timestamp
                }

            # 保存scaler
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Scaler保存成功: {scaler_path}")

            # 保存训练历史
            history_path = os.path.join(self.model_path, 'training_history.json')
            with open(history_path, 'w') as f:
                json.dump(self.history, f, indent=2)
            logger.info(f"训练历史保存成功: {history_path}")

            self.model_metadata['version'] = version
            self.model_metadata['last_updated'] = timestamp
            self.model_metadata['version_history'] = self.model_metadata.get('version_history', [])
            if version != 'latest':
                entry = {'version': version, 'timestamp': timestamp, 'models': dict(self.model_metadata['models'])}
                self.model_metadata['version_history'].append(entry)
                self.model_metadata['version_history'] = self.model_metadata['version_history'][-20:]

            self._save_model_metadata()

        except (IOError, OSError, ValueError, TypeError, pickle.PicklingError) as e:
            logger.error(f"保存模型失败 (version={version}): {e}", exc_info=True)
            raise
    
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
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"评估失败: {e}")
            return {}
    
    def generate_sample_data(self, n_samples=1000):
        """
        生成合成训练数据
        :param n_samples: 样本数量
        :return: 生成的时间序列数据
        """
        np.random.seed(42)
        t = np.arange(n_samples)
        
        # 生成周期性模式+噪声
        base_temp = 20 + 5 * np.sin(2 * np.pi * t / 24)  # 日周期
        weekly_pattern = 2 * np.sin(2 * np.pi * t / 168)  # 周周期
        noise = np.random.normal(0, 0.5, n_samples)
        temperature = base_temp + weekly_pattern + noise
        
        return temperature.tolist()
    
    def train_full_pipeline(self, training_data=None, epochs=50, batch_size=32, look_back=24, version=None):
        """
        完整的训练流程
        :param training_data: 训练数据，如果为None则生成样本数据
        :param epochs: 训练轮数
        :param batch_size: 批次大小
        :param look_back: 回溯窗口
        :param version: 模型版本号
        :return: 训练结果
        """
        try:
            logger.info("开始完整训练流程...")
            
            # 获取训练数据
            if training_data is None:
                logger.info("生成样本训练数据")
                training_data = self.generate_sample_data(1000)
            
            # 数据预处理
            data_array = np.array(training_data).reshape(-1, 1)
            scaled_data = self.scaler.fit_transform(data_array)
            
            # 准备训练和验证数据
            X, y = self.prepare_data(scaled_data, look_back=look_back)
            
            # 划分训练集和验证集
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # 构建和训练LSTM模型
            logger.info("训练LSTM模型...")
            self.lstm_model = Sequential([
                LSTM(64, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
                Dropout(0.3),
                LSTM(32, return_sequences=False),
                Dropout(0.3),
                Dense(16, activation='relu'),
                Dense(1)
            ])
            self.lstm_model.compile(optimizer='adam', loss='mean_squared_error')
            
            # 回调函数
            checkpoint = ModelCheckpoint(
                os.path.join(self.model_path, 'best_lstm_model.h5'),
                monitor='val_loss',
                save_best_only=True,
                mode='min',
                verbose=1
            )
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            )
            
            # 训练LSTM
            lstm_history = self.lstm_model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_val, y_val),
                callbacks=[checkpoint, early_stopping],
                verbose=1
            )
            
            # 使用LSTM的预测作为特征训练XGBoost
            logger.info("训练XGBoost模型...")
            lstm_train_pred = self.lstm_model.predict(X_train, verbose=0)
            lstm_val_pred = self.lstm_model.predict(X_val, verbose=0)
            
            self.xgb_model = XGBRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                n_jobs=-1,
                random_state=42
            )
            self.xgb_model.fit(
                lstm_train_pred, y_train,
                eval_set=[(lstm_val_pred, y_val)],
                early_stopping_rounds=20,
                verbose=True
            )
            
            # 评估模型
            train_eval = self._evaluate_model(X_train, y_train)
            val_eval = self._evaluate_model(X_val, y_val)
            
            # 保存训练历史
            training_record = {
                'timestamp': datetime.now().isoformat(),
                'version': version,
                'look_back': look_back,
                'epochs': epochs,
                'batch_size': batch_size,
                'train_metrics': train_eval,
                'val_metrics': val_eval,
                'lstm_history': {
                    'loss': [float(x) for x in lstm_history.history['loss']],
                    'val_loss': [float(x) for x in lstm_history.history['val_loss']]
                }
            }
            self.history.append(training_record)
            
            # 更新最佳分数
            val_rmse = val_eval['rmse']
            if val_rmse < self.best_score:
                self.best_score = val_rmse
            
            # 保存模型
            self.save_models(version=version)
            
            # 清空缓存
            prediction_cache.cache.clear()
            fusion_cache.cache.clear()
            
            logger.info(f"完整训练流程完成，验证集RMSE: {val_rmse}")
            
            return {
                'success': True,
                'version': version,
                'train_metrics': train_eval,
                'val_metrics': val_eval,
                'best_rmse': self.best_score
            }
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"完整训练流程失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _evaluate_model(self, X, y):
        """
        内部评估方法
        :param X: 特征
        :param y: 标签
        :return: 评估指标
        """
        if self.lstm_model is None or self.xgb_model is None:
            return {}
        
        lstm_pred = self.lstm_model.predict(X, verbose=0)
        xgb_pred = self.xgb_model.predict(lstm_pred)
        
        y_true = self.scaler.inverse_transform(y.reshape(-1, 1)).flatten()
        y_pred = self.scaler.inverse_transform(xgb_pred.reshape(-1, 1)).flatten()
        
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        return {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2)
        }
    
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
            eval_result = self._evaluate_model(X, y)
            current_score = eval_result.get('rmse', float('inf'))
            
            # 保存训练历史
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'rmse': current_score,
                'epochs': epochs
            })
            
            # 保存模型
            self.save_models()
            
            logger.info("模型自迭代改进完成")
            return {
                'success': True,
                'rmse': current_score,
                'best_rmse': self.best_score
            }
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"自迭代改进失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_model_info(self):
        """
        获取当前模型信息
        :return: 模型信息字典
        """
        info = {
            'model_path': self.model_path,
            'best_rmse': self.best_score,
            'history_count': len(self.history),
            'metadata': self.model_metadata,
            'models_loaded': {
                'lstm': self.lstm_model is not None,
                'xgb': self.xgb_model is not None,
                'gpr': self.gpr_model is not None,
                'convlstm': self.convlstm_model is not None
            }
        }
        if self.history:
            info['latest_training'] = self.history[-1]
        return info
    
    def load_wrf_data(self, wrf_data):
        """
        加载WRF数据
        :param wrf_data: WRF数据
        """
        try:
            self.wrf_data = wrf_data
            logger.info("WRF数据加载成功")
            return True
        except (ValueError, KeyError, TypeError, AttributeError) as e:
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
        except (ValueError, KeyError, TypeError, AttributeError) as e:
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
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
            
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
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
        logger.debug(json.dumps({
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
            logger.debug(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            predictions = model.predict(input_data)
            logger.info("预测完成")
            logger.debug(json.dumps({
                'success': True,
                'data': predictions
            }))
        except (ValueError, IndexError, KeyError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"预测失败: {e}")
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'correct':
        # 订正命令
        if len(sys.argv) < 4:
            logger.error("缺少预测数据和观测数据")
            logger.debug(json.dumps({
                'success': False,
                'error': '缺少预测数据和观测数据'
            }))
            return
        
        try:
            forecast_data = load_input(2)
            observed_data = load_input(3)
            corrected_data = model.correct(forecast_data, observed_data)
            logger.debug(json.dumps({
                'success': True,
                'data': corrected_data
            }))
        except (ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError, AttributeError) as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'train':
        # 训练命令
        if len(sys.argv) < 3:
            logger.debug(json.dumps({
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
            logger.debug(json.dumps({
                'success': True,
                'message': '模型训练完成'
            }))
        except (ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError, AttributeError) as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'train_full':
        # 完整训练命令
        if len(sys.argv) < 3:
            logger.debug(json.dumps({
                'success': False,
                'error': '缺少训练配置'
            }))
            return
        
        try:
            config = load_input(2)
            training_data = config.get('data')
            epochs = config.get('epochs', 50)
            batch_size = config.get('batch_size', 32)
            look_back = config.get('look_back', 24)
            version = config.get('version')
            
            result = model.train_full_pipeline(
                training_data=training_data,
                epochs=epochs,
                batch_size=batch_size,
                look_back=look_back,
                version=version
            )
            logger.debug(json.dumps(result))
        except (ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError, AttributeError) as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'improve':
        # 自迭代改进命令
        if len(sys.argv) < 3:
            logger.debug(json.dumps({
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
            logger.debug(json.dumps({
                'success': result['success'],
                'data': result
            }))
        except (ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError, AttributeError) as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'fusion':
        # 双预报引擎融合预测命令
        if len(sys.argv) < 3:
            logger.debug(json.dumps({
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
            logger.debug(json.dumps({
                'success': True,
                'data': predictions
            }))
        except (ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError, AttributeError) as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'risk':
        # 生成风险热力图命令
        if len(sys.argv) < 3:
            logger.debug(json.dumps({
                'success': False,
                'error': '缺少预测数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            forecast_data = input_data.get('forecast_data', [])
            
            # 生成风险热力图
            risk_data = model.generate_risk_heatmap(forecast_data)
            logger.debug(json.dumps({
                'success': True,
                'data': risk_data
            }))
        except (ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError, AttributeError) as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'model_info':
        # 获取模型信息
        try:
            info = model.get_model_info()
            logger.debug(json.dumps({
                'success': True,
                'data': info
            }))
        except Exception as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'save_models':
        # 手动保存模型
        try:
            version = sys.argv[3] if len(sys.argv) > 3 else None
            model.save_models(version=version)
            logger.debug(json.dumps({
                'success': True,
                'message': '模型保存成功'
            }))
        except Exception as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'load_models':
        # 加载指定版本的模型
        try:
            version = sys.argv[3] if len(sys.argv) > 3 else None
            model.load_models(model_version=version)
            logger.debug(json.dumps({
                'success': True,
                'message': '模型加载成功'
            }))
        except Exception as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'get_forecast':
        # 获取预报数据（模拟接口）
        try:
            params = load_input(2)
            lat = params.get('lat', 39.9)
            lng = params.get('lng', 116.4)
            hours = params.get('hours', 24)
            
            # 生成模拟预报数据
            forecast = []
            base_temp = 20 + np.random.normal(0, 2)
            for i in range(hours):
                hour_temp = base_temp + 5 * np.sin(2 * np.pi * i / 24) + np.random.normal(0, 0.5)
                forecast.append({
                    'hour': i,
                    'temperature': float(hour_temp),
                    'humidity': float(50 + np.random.normal(0, 10)),
                    'wind_speed': float(5 + np.random.normal(0, 2)),
                    'wind_direction': float(180 + np.random.normal(0, 30))
                })
            
            logger.debug(json.dumps({
                'success': True,
                'data': forecast,
                'metadata': {'lat': lat, 'lng': lng, 'hours': hours}
            }))
        except Exception as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'get_realtime_weather':
        # 获取实时天气（模拟接口）
        try:
            params = load_input(2)
            lat = params.get('lat', 39.9)
            lng = params.get('lng', 116.4)
            
            weather = {
                'temperature': float(22 + np.random.normal(0, 1)),
                'humidity': float(55 + np.random.normal(0, 5)),
                'wind_speed': float(6 + np.random.normal(0, 1)),
                'wind_direction': float(200 + np.random.normal(0, 10)),
                'pressure': float(1013 + np.random.normal(0, 5)),
                'visibility': float(10 + np.random.normal(0, 2)),
                'timestamp': datetime.now().isoformat(),
                'location': {'lat': lat, 'lng': lng}
            }
            
            logger.debug(json.dumps({
                'success': True,
                'data': weather
            }))
        except Exception as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    elif command == 'get_detailed_forecast':
        # 获取详细预报（模拟接口）
        try:
            params = load_input(2)
            hours = params.get('hours', 72)
            
            detailed_forecast = []
            for day in range(hours // 24):
                day_forecast = {
                    'day': day + 1,
                    'date': (datetime.now() + pd.Timedelta(days=day)).strftime('%Y-%m-%d'),
                    'max_temp': float(28 + np.random.normal(0, 3)),
                    'min_temp': float(18 + np.random.normal(0, 2)),
                    'weather': ['晴', '多云', '阴', '小雨'][np.random.randint(4)],
                    'wind': f'{int(3 + np.random.randint(5))}级 {["东北", "东南", "西南", "西北"][np.random.randint(4)]}风'
                }
                detailed_forecast.append(day_forecast)
            
            logger.debug(json.dumps({
                'success': True,
                'data': detailed_forecast
            }))
        except Exception as e:
            logger.debug(json.dumps({
                'success': False,
                'error': str(e)
            }))
    
    else:
        logger.debug(json.dumps({
            'success': False,
            'error': '未知命令'
        }))

if __name__ == "__main__":
    main()
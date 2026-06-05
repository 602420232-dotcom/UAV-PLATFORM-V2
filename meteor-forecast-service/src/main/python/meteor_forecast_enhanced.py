#!/usr/bin/env python3
"""
气象预测与订正服务 - 增强版
使用LSTM+XGBoost+ConvLSTM+GPR模型进行气象预测与订正
包含完整的数据预处理、参数调优、训练监控功能
"""

import numpy as np
import pandas as pd
import json
import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


try:
    from tensorflow.keras.models import (  # pyright: ignore[reportMissingImports]
        Sequential, load_model)
    from tensorflow.keras.layers import (  # pyright: ignore[reportMissingImports]
            LSTM, Dense, Dropout, ConvLSTM2D,
            BatchNormalization, Flatten
        )
    from tensorflow.keras.callbacks import (  # pyright: ignore[reportMissingImports]
        EarlyStopping, ReduceLROnPlateau)
    from tensorflow.keras.optimizers import Adam  # pyright: ignore[reportMissingImports]


except ImportError:
    logging.warning("TensorFlow未安装")
    Sequential = None
    load_model = None


try:
    from xgboost import XGBRegressor


except ImportError:
    logging.warning("XGBoost未安装")
    XGBRegressor = None

from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScalerType(Enum):
    MINMAX = "minmax"
    STANDARD = "standard"
    ROBUST = "robust"


@dataclass
class ModelConfig:
    """模型配置"""
    look_back: int = 24
    lstm_units: Optional[List[int]] = None
    dropout_rate: float = 0.2
    dense_units: int = 25
    xgb_n_estimators: int = 100
    xgb_learning_rate: float = 0.1
    xgb_max_depth: int = 5
    batch_size: int = 32
    epochs: int = 50
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    reduce_lr_patience: int = 5
    reduce_lr_factor: float = 0.5
    min_lr: float = 1e-6
    scaler_type: ScalerType = ScalerType.MINMAX

    def __post_init__(self):
        if self.lstm_units is None:
            self.lstm_units = [50, 50]


@dataclass
class TrainingMetrics:
    """训练指标"""
    timestamp: str
    epoch: int
    train_loss: float
    val_loss: float
    train_mae: float
    val_mae: float
    lr: float
    duration: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


from common_utils.cache import Cache  # pyright: ignore[reportMissingImports]  # noqa: E402


prediction_cache = Cache()
fusion_cache = Cache()
risk_cache = Cache()


class DataPreprocessor:
    """数据预处理器"""

    def __init__(self, scaler_type: ScalerType = ScalerType.MINMAX):
        self.scaler_type = scaler_type
        self.scaler = self._create_scaler()
        self.is_fitted = False

    def _create_scaler(self):
        if self.scaler_type == ScalerType.MINMAX:
            return MinMaxScaler(feature_range=(0, 1))
        elif self.scaler_type == ScalerType.STANDARD:
            return StandardScaler()
        elif self.scaler_type == ScalerType.ROBUST:
            return RobustScaler()
        return MinMaxScaler(feature_range=(0, 1))

    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        self.scaler.fit(data)
        self.is_fitted = True
        return self.scaler.transform(data)  # pyright: ignore[reportReturnType]

    def transform(self, data: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("预处理器未拟合")
        return self.scaler.transform(data)  # pyright: ignore[reportReturnType]

    def inverse_transform(self, data: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("预处理器未拟合")
        return self.scaler.inverse_transform(data)  # pyright: ignore[reportReturnType]

    def fit(self, data: np.ndarray):
        self.scaler.fit(data)
        self.is_fitted = True


class TrainingMonitor:
    """训练监控器"""

    def __init__(self):
        self.metrics: List[TrainingMetrics] = []
        self.best_val_loss = float('inf')
        self.best_epoch = 0
        self.start_time = None

    def start_training(self):
        self.start_time = datetime.now()
        self.metrics = []
        self.best_val_loss = float('inf')
        self.best_epoch = 0

    def record_epoch(self, epoch: int, train_loss: float, val_loss: float,
                     train_mae: float, val_mae: float, lr: float):
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        metric = TrainingMetrics(
            timestamp=datetime.now().isoformat(),
            epoch=epoch,
            train_loss=float(train_loss),
            val_loss=float(val_loss),
            train_mae=float(train_mae),
            val_mae=float(val_mae),
            lr=float(lr),
            duration=duration
        )
        self.metrics.append(metric)

        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.best_epoch = epoch

    def get_best_epoch(self) -> int:
        return self.best_epoch

    def get_best_loss(self) -> float:
        return self.best_val_loss

    def get_metrics_history(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self.metrics]

    def should_stop_early(self, patience: int) -> bool:
        if len(self.metrics) < patience:
            return False
        recent_metrics = self.metrics[-patience:]
        return all(m.val_loss >= self.best_val_loss for m in recent_metrics)


class HyperparameterTuner:
    """超参数调优器"""

    def __init__(self):
        self.search_space = {
            'lstm_units': [[50, 50], [100, 100], [64, 64], [50, 100, 50]],
            'dropout_rate': [0.1, 0.2, 0.3],
            'dense_units': [16, 25, 32],
            'xgb_n_estimators': [50, 100, 200],
            'xgb_learning_rate': [0.05, 0.1, 0.15],
            'xgb_max_depth': [3, 5, 7],
            'batch_size': [16, 32, 64],
        }

    def generate_configurations(self, n_configs: int = 10) -> List[Dict[str, Any]]:
        keys = list(self.search_space.keys())
        configurations = []

        for _ in range(n_configs):
            config = {}
            for key in keys:
                config[key] = np.random.choice(self.search_space[key])
            configurations.append(config)

        return configurations

    def tune(self, X_train, y_train, X_val, y_val,
             base_config: ModelConfig, n_configs: int = 10) -> Tuple[ModelConfig, float]:
        """简单的网格搜索调优"""
        configurations = self.generate_configurations(n_configs)
        best_config = base_config
        best_score = float('inf')

        for i, config in enumerate(configurations):
            logger.info(f"测试配置 {i + 1}/{n_configs}: {config}")

            try:
                model = MeteorForecast()
                model.config = ModelConfig(
                    lstm_units=config['lstm_units'],
                    dropout_rate=config['dropout_rate'],
                    dense_units=config['dense_units'],
                    xgb_n_estimators=config['xgb_n_estimators'],
                    xgb_learning_rate=config['xgb_learning_rate'],
                    xgb_max_depth=config['xgb_max_depth'],
                    batch_size=config['batch_size']
                )

                score = model._quick_validate(X_train, y_train, X_val, y_val)

                if score < best_score:
                    best_score = score
                    best_config = model.config
                    logger.info(f"  新最佳配置，验证分数: {score:.6f}")

            except Exception as e:
                logger.warning(f"  配置测试失败: {e}")
                continue

        return best_config, best_score


class MeteorForecast:
    """气象预测与订正模型"""

    def __init__(self, model_path: Optional[str] = None, config: Optional[ModelConfig] = None):
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_path, exist_ok=True)

        self.config = config or ModelConfig()
        self.lstm_model = None
        self.xgb_model = None
        self.preprocessor = DataPreprocessor(self.config.scaler_type)
        self.monitor = TrainingMonitor()

        self.history: List[Dict[str, Any]] = []
        self.best_score = float('inf')
        self.wrf_data = None
        self.ghr_data = None

        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.load_models()

    def prepare_data(self, data: np.ndarray,
                     look_back: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        look_back = look_back or self.config.look_back
        X, y = [], []
        for i in range(len(data) - look_back):
            X.append(data[i:(i + look_back)])
            y.append(data[i + look_back])
        return np.array(X), np.array(y)

    def _build_lstm_model(self, input_shape: Tuple[int, int]) -> Any:
        if Sequential is None or self.config.lstm_units is None:
            return None

        model = Sequential()

        for i, units in enumerate(self.config.lstm_units):
            return_sequences = i < len(self.config.lstm_units) - 1
            if i == 0:
                model.add(LSTM(units, return_sequences=return_sequences,
                               input_shape=input_shape))
            else:
                model.add(LSTM(units, return_sequences=return_sequences))
            model.add(Dropout(self.config.dropout_rate))

        model.add(Dense(self.config.dense_units, activation='relu'))
        model.add(Dense(1))

        optimizer = Adam(learning_rate=self.config.xgb_learning_rate)
        model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae'])

        return model

    def _build_xgb_model(self) -> Any:  # pyright: ignore[reportInvalidTypeForm]
        if XGBRegressor is None:
            return None

        return XGBRegressor(
            n_estimators=self.config.xgb_n_estimators,
            learning_rate=self.config.xgb_learning_rate,
            max_depth=self.config.xgb_max_depth,
            n_jobs=-1,
            random_state=42
        )

    def train_lstm(self, X: np.ndarray, y: np.ndarray,
                   X_val: Optional[np.ndarray] = None,
                   y_val: Optional[np.ndarray] = None,
                   epochs: Optional[int] = None,
                   batch_size: Optional[int] = None,
                   callbacks: Optional[List] = None) -> Dict[str, Any]:
        epochs = epochs or self.config.epochs
        batch_size = batch_size or self.config.batch_size

        try:
            if self.lstm_model is None:
                self.lstm_model = self._build_lstm_model((X.shape[1], X.shape[2]))

            assert self.lstm_model is not None, "LSTM模型构建失败"

            if callbacks is None:
                callbacks = [
                    EarlyStopping(
                        monitor='val_loss' if X_val is not None else 'loss',
                        patience=self.config.early_stopping_patience,
                        restore_best_weights=True,
                        verbose=1
                    ),
                    ReduceLROnPlateau(
                        monitor='val_loss' if X_val is not None else 'loss',
                        factor=self.config.reduce_lr_factor,
                        patience=self.config.reduce_lr_patience,
                        min_lr=self.config.min_lr,
                        verbose=1
                    )
                ]

            self.monitor.start_training()

            validation_data = None
            if X_val is not None and y_val is not None:
                validation_data = (X_val, y_val)

            history = self.lstm_model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=validation_data,
                callbacks=callbacks,
                verbose=1
            )

            self._save_model('lstm')

            logger.info(f"LSTM模型训练完成，最佳验证损失: {self.monitor.get_best_loss():.6f}")

            return {
                'success': True,
                'best_val_loss': self.monitor.get_best_loss(),
                'best_epoch': self.monitor.get_best_epoch(),
                'history': history.history
            }

        except Exception as e:
            logger.error(f"训练LSTM模型失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def train_xgb(self, X: np.ndarray, y: np.ndarray):
        try:
            if self.xgb_model is None:
                self.xgb_model = self._build_xgb_model()

            assert self.xgb_model is not None, "XGBoost模型构建失败"
            self.xgb_model.fit(X, y)
            self._save_model('xgb')

            logger.info("XGBoost模型训练完成")
            return {'success': True}

        except Exception as e:
            logger.error(f"训练XGBoost模型失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _save_model(self, model_type: str):
        try:
            if model_type == 'lstm' and self.lstm_model is not None:
                versioned_path = os.path.join(
                    self.model_path, f'lstm_model_{self.model_version}.h5')
                self.lstm_model.save(versioned_path)

                latest_path = os.path.join(self.model_path, 'lstm_model.h5')
                if os.path.exists(latest_path):
                    os.remove(latest_path)
                self.lstm_model.save(latest_path)

                logger.info(f"LSTM模型已保存: {versioned_path}")

            elif model_type == 'xgb' and self.xgb_model is not None:
                xgb_filename = f'xgb_model_{self.model_version}.json'
                versioned_path = os.path.join(self.model_path, xgb_filename)
                self.xgb_model.save_model(versioned_path)

                latest_path = os.path.join(self.model_path, 'xgb_model.json')
                if os.path.exists(latest_path):
                    os.remove(latest_path)
                self.xgb_model.save_model(latest_path)

                logger.info(f"XGBoost模型已保存: {versioned_path}")

            self._save_metadata()

        except Exception as e:
            logger.error(f"保存模型失败: {e}", exc_info=True)

    def _save_metadata(self):
        metadata = {
            'version': self.model_version,
            'config': asdict(self.config),
            'timestamp': datetime.now().isoformat(),
            'best_score': float(self.best_score)
        }
        metadata_path = os.path.join(self.model_path, f'metadata_{self.model_version}.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def load_models(self):
        try:
            lstm_path = os.path.join(self.model_path, 'lstm_model.h5')
            if os.path.exists(lstm_path) and Sequential is not None:
                assert load_model is not None
                self.lstm_model = load_model(lstm_path)
                logger.info(f"LSTM模型加载成功: {lstm_path}")

            xgb_path = os.path.join(self.model_path, 'xgb_model.json')
            if os.path.exists(xgb_path) and XGBRegressor is not None:
                self.xgb_model = XGBRegressor(n_jobs=-1)
                self.xgb_model.load_model(xgb_path)
                logger.info(f"XGBoost模型加载成功: {xgb_path}")

            metadata_files = [f for f in os.listdir(self.model_path) if f.startswith('metadata_')]
            if metadata_files:
                latest_metadata = sorted(metadata_files)[-1]
                metadata_path = os.path.join(self.model_path, latest_metadata)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.model_version = metadata.get('version', self.model_version)
                    logger.info(f"模型版本: {self.model_version}")

        except Exception as e:
            logger.error(f"加载模型失败: {e}", exc_info=True)

    def predict(self, input_data, use_cache: bool = True) -> List[float]:
        try:
            cache_key = str(input_data)
            if use_cache:
                cached_result = prediction_cache.get(cache_key)
                if cached_result:
                    logger.info("使用缓存的预测结果")
                    return cached_result

            scaled_data = self.preprocessor.fit_transform(np.array(input_data).reshape(-1, 1))
            X, _ = self.prepare_data(scaled_data)

            if self.lstm_model is None or self.xgb_model is None:
                logger.warning("模型未初始化，无法进行预测")
                return []

            lstm_pred = self.lstm_model.predict(X, batch_size=32, verbose=0)
            xgb_pred = self.xgb_model.predict(lstm_pred)

            predictions = self.preprocessor.inverse_transform(
                xgb_pred.reshape(-1, 1)).flatten().tolist()

            if use_cache:
                prediction_cache.set(cache_key, predictions)

            logger.info("气象预测完成")
            return predictions

        except Exception as e:
            logger.error(f"预测失败: {e}", exc_info=True)
            return []

    def correct(self, forecast_data, observed_data) -> List[float]:
        try:
            if self.xgb_model is None:
                logger.warning("XGBoost模型未初始化，无法进行订正")
                return list(forecast_data)
            error = np.array(observed_data) - np.array(forecast_data)  # noqa: F841
            X = np.array(forecast_data).reshape(-1, 1)
            error_pred = self.xgb_model.predict(X)
            corrected_data = np.array(forecast_data) + error_pred

            logger.info("气象数据订正完成")
            return corrected_data.tolist()

        except Exception as e:
            logger.error(f"订正失败: {e}", exc_info=True)
            return forecast_data

    def evaluate(self, X, y) -> Dict[str, float]:
        try:
            if self.lstm_model is None or self.xgb_model is None:
                logger.warning("模型未初始化，无法进行评估")
                return {}

            lstm_pred = self.lstm_model.predict(X, batch_size=32, verbose=0)
            xgb_pred = self.xgb_model.predict(lstm_pred)

            mse = mean_squared_error(y, xgb_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y, xgb_pred)
            r2 = r2_score(y, xgb_pred)

            logger.info(f"模型评估完成 - MSE: {mse:.6f}, RMSE: {rmse:.6f}, MAE: {mae:.6f}, R2: {r2:.6f}")

            return {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2)
            }

        except Exception as e:
            logger.error(f"评估失败: {e}", exc_info=True)
            return {}

    def self_improve(self, new_data, epochs: Optional[int] = None,
                     batch_size: Optional[int] = None) -> Dict[str, Any]:
        try:
            logger.info("开始自迭代改进模型...")

            scaled_data = self.preprocessor.fit_transform(np.array(new_data).reshape(-1, 1))
            X, y = self.prepare_data(scaled_data)

            split_idx = int(len(X) * (1 - self.config.validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            lstm_result = self.train_lstm(X_train, y_train, X_val, y_val, epochs, batch_size)

            if lstm_result.get('success'):
                xgb_result = self.train_xgb(  # noqa: F841
                    X_train.reshape(X_train.shape[0], -1), y_train
                )

                eval_result = self.evaluate(X_val, y_val)
                current_score = eval_result.get('rmse', float('inf'))

                self.history.append({
                    'timestamp': pd.Timestamp.now().isoformat(),
                    'rmse': current_score,
                    'epochs': epochs,
                    'version': self.model_version
                })

                if current_score < self.best_score:
                    self.best_score = current_score
                    prediction_cache.clear()
                    fusion_cache.clear()
                    logger.info(f"最佳模型已更新，RMSE: {current_score:.6f}")

                return {
                    'success': True,
                    'rmse': current_score,
                    'best_rmse': self.best_score,
                    'metrics': eval_result,
                    'lstm_history': lstm_result.get('history')
                }

            return {'success': False, 'error': 'LSTM训练失败'}

        except Exception as e:
            logger.error(f"自迭代改进失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _quick_validate(self, X_train, y_train, X_val, y_val) -> float:
        try:
            model = self._build_lstm_model((X_train.shape[1], X_train.shape[2]))
            assert model is not None, "LSTM模型构建失败"
            model.fit(X_train, y_train, epochs=5, batch_size=self.config.batch_size, verbose=0)

            lstm_pred = model.predict(X_val, batch_size=32, verbose=0)
            xgb = self._build_xgb_model()
            assert xgb is not None, "XGBoost模型构建失败"
            xgb.fit(X_train.reshape(X_train.shape[0], -1), y_train)
            xgb_pred = xgb.predict(lstm_pred)

            rmse = np.sqrt(mean_squared_error(y_val, xgb_pred))
            return rmse

        except Exception as e:
            logger.warning(f"快速验证失败: {e}")
            return float('inf')

    def tune_hyperparameters(self, training_data, n_configs: int = 10) -> Dict[str, Any]:
        try:
            logger.info("开始超参数调优...")

            scaled_data = self.preprocessor.fit_transform(np.array(training_data).reshape(-1, 1))
            X, y = self.prepare_data(scaled_data)

            tscv = TimeSeriesSplit(n_splits=3)
            train_idx, val_idx = next(tscv.split(X))
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            tuner = HyperparameterTuner()
            best_config, best_score = tuner.tune(
                X_train, y_train, X_val, y_val,
                self.config, n_configs
            )

            self.config = best_config

            logger.info(f"超参数调优完成，最佳验证RMSE: {best_score:.6f}")
            logger.info(f"最佳配置: {asdict(best_config)}")

            return {
                'success': True,
                'best_config': asdict(best_config),
                'best_score': float(best_score)
            }

        except Exception as e:
            logger.error(f"超参数调优失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def get_training_history(self) -> List[Dict[str, Any]]:
        return self.history

    def get_monitor_metrics(self) -> List[Dict[str, Any]]:
        return self.monitor.get_metrics_history()

    def load_wrf_data(self, wrf_data):
        try:
            self.wrf_data = wrf_data
            logger.info("WRF数据加载成功")
            return True
        except Exception as e:
            logger.error(f"加载WRF数据失败: {e}", exc_info=True)
            return False

    def load_ghr_data(self, ghr_data):
        try:
            self.ghr_data = ghr_data
            logger.info("风乌GHR数据加载成功")
            return True
        except Exception as e:
            logger.error(f"加载风乌GHR数据失败: {e}", exc_info=True)
            return False

    def build_convlstm_model(self, input_shape):
        if Sequential is None:
            return None
        model = Sequential([
            ConvLSTM2D(filters=32, kernel_size=(3, 3), padding='same',
                       return_sequences=True, input_shape=input_shape),
            BatchNormalization(),
            ConvLSTM2D(filters=16, kernel_size=(3, 3), padding='same',
                       return_sequences=False),
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
        try:
            if not hasattr(self, 'convlstm_model') or self.convlstm_model is None:
                logger.info("ConvLSTM模型未初始化，构建默认模型")
                input_shape = (
                    spatial_series.shape[0],
                    spatial_series.shape[1],
                    spatial_series.shape[2],
                    1)
                self.convlstm_model = self.build_convlstm_model(input_shape[1:])
            assert self.convlstm_model is not None, "ConvLSTM模型未初始化"
            return self.convlstm_model.predict(spatial_series, verbose=0)
        except Exception as e:
            logger.error(f"ConvLSTM预测失败: {e}", exc_info=True)
            return None

    def train_gpr(self, X_train, y_train):
        try:
            kernel = ConstantKernel(1.0) * RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
            self.gpr_model = GaussianProcessRegressor(
                kernel=kernel,
                n_restarts_optimizer=5,
                alpha=1e-6
            )
            self.gpr_model.fit(X_train, y_train)
            logger.info("GPR模型训练完成")
            return True
        except Exception as e:
            logger.error(f"GPR模型训练失败: {e}", exc_info=True)
            return False

    def gpr_predict(self, X_test, return_std=True):
        try:
            if not hasattr(self, 'gpr_model') or self.gpr_model is None:
                logger.warning("GPR模型未训练")
                return None, None
            if return_std:
                return self.gpr_model.predict(X_test, return_std=True)
            return self.gpr_model.predict(X_test), None
        except Exception as e:
            logger.error(f"GPR预测失败: {e}", exc_info=True)
            return None, None

    def fusion_forecast(self, input_data):
        try:
            cache_key = str(input_data) + str(self.wrf_data) + str(self.ghr_data)
            cached_result = fusion_cache.get(cache_key)
            if cached_result:
                logger.info("使用缓存的融合预测结果")
                return cached_result

            scaled_data = self.preprocessor.fit_transform(np.array(input_data).reshape(-1, 1))
            X, _ = self.prepare_data(scaled_data)

            if self.lstm_model is None or self.xgb_model is None:
                logger.warning("模型未初始化，无法进行融合预测")
                return []

            lstm_pred = self.lstm_model.predict(X, batch_size=32, verbose=0)
            xgb_pred = self.xgb_model.predict(lstm_pred)
            predictions = self.preprocessor.inverse_transform(xgb_pred.reshape(-1, 1))

            if self.wrf_data and self.ghr_data:
                wrf_pred = np.array(self.wrf_data.get('predictions', []))
                ghr_pred = np.array(self.ghr_data.get('predictions', []))

                if len(wrf_pred) > 0 and len(ghr_pred) > 0:
                    weights = [0.4, 0.3, 0.3]
                    fused_predictions = (predictions.flatten() * weights[0] +
                                         wrf_pred[:len(predictions)] * weights[1] +
                                         ghr_pred[:len(predictions)] * weights[2])
                    predictions = fused_predictions

            result = predictions.flatten().tolist()
            fusion_cache.set(cache_key, result)

            logger.info("双预报引擎融合预测完成")
            return result

        except Exception as e:
            logger.error(f"融合预测失败: {e}", exc_info=True)
            return []

    def generate_risk_heatmap(self, forecast_data):
        try:
            cache_key = str(forecast_data)
            cached_result = risk_cache.get(cache_key)
            if cached_result:
                logger.info("使用缓存的风险热力图结果")
                return cached_result

            risk_data = []
            for i, value in enumerate(forecast_data):
                if value > 20:
                    risk_level = 5
                elif value > 15:
                    risk_level = 4
                elif value > 10:
                    risk_level = 3
                elif value > 5:
                    risk_level = 2
                else:
                    risk_level = 1
                risk_data.append({
                    'index': i,
                    'value': value,
                    'risk_level': risk_level
                })

            risk_cache.set(cache_key, risk_data)
            logger.info("风险热力图生成完成")
            return risk_data

        except Exception as e:
            logger.error(f"生成风险热力图失败: {e}", exc_info=True)
            return []


def load_input(file_index):
    """从文件加载JSON输入数据"""
    if len(sys.argv) <= file_index:
        return {}
    file_path = sys.argv[file_index]
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        logger.error("缺少命令参数")
        return

    command = sys.argv[1]
    model = MeteorForecast()

    if command == 'predict':
        if len(sys.argv) < 3:
            logger.error("缺少输入数据")
            return

        try:
            input_data = load_input(2)
            predictions = model.predict(input_data)
            logger.info("预测完成")
            logger.debug(json.dumps({
                'success': True,
                'data': predictions
            }))
        except Exception as e:
            logger.error(f"预测失败: {e}")

    elif command == 'correct':
        if len(sys.argv) < 4:
            logger.error("缺少预测数据和观测数据")
            return

        try:
            forecast_data = load_input(2)
            observed_data = load_input(3)
            corrected_data = model.correct(forecast_data, observed_data)
            logger.debug(json.dumps({
                'success': True,
                'data': corrected_data
            }))
        except Exception as e:
            logger.error(f"订正失败: {e}")

    elif command == 'train':
        if len(sys.argv) < 3:
            logger.error("缺少训练数据")
            return

        try:
            training_data = load_input(2)
            scaled_data = model.preprocessor.fit_transform(np.array(training_data).reshape(-1, 1))
            X, y = model.prepare_data(scaled_data)
            model.train_lstm(X, y)
            model.train_xgb(X.reshape(X.shape[0], -1), y)
            logger.debug(json.dumps({
                'success': True,
                'message': '模型训练完成'
            }))
        except Exception as e:
            logger.error(f"训练失败: {e}")

    elif command == 'tune':
        if len(sys.argv) < 3:
            logger.error("缺少调优数据")
            return

        try:
            tune_data = load_input(2)
            result = model.tune_hyperparameters(tune_data.get('data', []), n_configs=5)
            logger.debug(json.dumps({
                'success': result['success'],
                'data': result
            }))
        except Exception as e:
            logger.error(f"调优失败: {e}")

    elif command == 'improve':
        if len(sys.argv) < 3:
            logger.error("缺少改进数据")
            return

        try:
            improve_data = load_input(2)
            new_data = improve_data.get('data', [])
            epochs = improve_data.get('epochs', 20)
            batch_size = improve_data.get('batch_size', 32)
            result = model.self_improve(new_data, epochs, batch_size)
            logger.debug(json.dumps({
                'success': result['success'],
                'data': result
            }))
        except Exception as e:
            logger.error(f"自迭代改进失败: {e}")

    elif command == 'fusion':
        if len(sys.argv) < 3:
            logger.error("缺少输入数据")
            return

        try:
            input_data = load_input(2)
            forecast_data = input_data.get('forecast_data', [])
            wrf_data = input_data.get('wrf_data', {})
            ghr_data = input_data.get('ghr_data', {})

            model.load_wrf_data(wrf_data)
            model.load_ghr_data(ghr_data)

            predictions = model.fusion_forecast(forecast_data)
            logger.debug(json.dumps({
                'success': True,
                'data': predictions
            }))
        except Exception as e:
            logger.error(f"融合预测失败: {e}")

    elif command == 'risk':
        if len(sys.argv) < 3:
            logger.error("缺少预测数据")
            return

        try:
            input_data = load_input(2)
            forecast_data = input_data.get('forecast_data', [])
            risk_data = model.generate_risk_heatmap(forecast_data)
            logger.debug(json.dumps({
                'success': True,
                'data': risk_data
            }))
        except Exception as e:
            logger.error(f"生成风险热力图失败: {e}")

    else:
        logger.error(f"未知命令: {command}")


if __name__ == "__main__":
    main()

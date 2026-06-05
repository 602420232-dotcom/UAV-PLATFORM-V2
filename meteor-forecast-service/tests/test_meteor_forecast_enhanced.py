"""
LSTM+XGBoost气象预测模型单元测试
"""

import pytest
import numpy as np
import os
import tempfile
import shutil


try:
    from meteor_forecast_enhanced import (
        MeteorForecast,
        DataPreprocessor,
        TrainingMonitor,
        ModelConfig,
        ScalerType
    )
    ENHANCED_MODEL_AVAILABLE = True


except ImportError:
    ENHANCED_MODEL_AVAILABLE = False


class TestDataPreprocessor:
    """数据预处理器测试"""

    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        return np.random.rand(100, 1) * 100

    def test_minmax_scaler(self, sample_data):
        """测试MinMax缩放器"""
        preprocessor = DataPreprocessor(ScalerType.MINMAX)
        scaled = preprocessor.fit_transform(sample_data)

        assert scaled.min() >= 0
        assert scaled.max() <= 1
        assert scaled.shape == sample_data.shape

    def test_standard_scaler(self, sample_data):
        """测试Standard缩放器"""
        preprocessor = DataPreprocessor(ScalerType.STANDARD)
        scaled = preprocessor.fit_transform(sample_data)

        assert abs(scaled.mean()) < 1e-10
        assert abs(scaled.std() - 1.0) < 1e-10

    def test_robust_scaler(self, sample_data):
        """测试Robust缩放器"""
        preprocessor = DataPreprocessor(ScalerType.ROBUST)
        scaled = preprocessor.fit_transform(sample_data)

        assert scaled.shape == sample_data.shape

    def test_inverse_transform(self, sample_data):
        """测试反变换"""
        preprocessor = DataPreprocessor()
        scaled = preprocessor.fit_transform(sample_data)
        inversed = preprocessor.inverse_transform(scaled)

        np.testing.assert_array_almost_equal(sample_data, inversed, decimal=10)

    def test_fit_without_transform(self):
        """测试只拟合不变换"""
        preprocessor = DataPreprocessor()
        data = np.random.rand(50, 1) * 50

        preprocessor.fit(data)
        assert preprocessor.is_fitted is True

    def test_transform_without_fit(self):
        """测试未拟合就变换"""
        preprocessor = DataPreprocessor()
        data = np.random.rand(50, 1) * 50

        with pytest.raises(ValueError, match="预处理器未拟合"):
            preprocessor.transform(data)


class TestTrainingMonitor:
    """训练监控器测试"""

    def test_monitor_initialization(self):
        """测试监控器初始化"""
        monitor = TrainingMonitor()

        assert monitor.best_val_loss == float('inf')
        assert monitor.best_epoch == 0
        assert monitor.start_time is None
        assert len(monitor.metrics) == 0

    def test_record_epoch(self):
        """测试记录训练周期"""
        monitor = TrainingMonitor()
        monitor.start_training()

        monitor.record_epoch(
            epoch=1,
            train_loss=0.5,
            val_loss=0.4,
            train_mae=0.3,
            val_mae=0.2,
            lr=0.001
        )

        assert len(monitor.metrics) == 1
        assert monitor.metrics[0].epoch == 1
        assert monitor.best_val_loss == 0.4
        assert monitor.best_epoch == 1

    def test_best_loss_tracking(self):
        """测试最佳损失跟踪"""
        monitor = TrainingMonitor()
        monitor.start_training()

        monitor.record_epoch(1, 0.5, 0.4, 0.3, 0.2, 0.001)
        monitor.record_epoch(2, 0.4, 0.3, 0.2, 0.1, 0.001)
        monitor.record_epoch(3, 0.3, 0.35, 0.2, 0.15, 0.001)

        assert monitor.get_best_loss() == 0.3
        assert monitor.get_best_epoch() == 2

    def test_early_stopping(self):
        """测试早停判断"""
        monitor = TrainingMonitor()
        monitor.start_training()

        for i in range(5):
            monitor.record_epoch(i+1, 0.5, 0.4, 0.3, 0.2, 0.001)

        assert monitor.should_stop_early(patience=3) is True
        assert monitor.should_stop_early(patience=5) is False

    def test_get_metrics_history(self):
        """测试获取指标历史"""
        monitor = TrainingMonitor()
        monitor.start_training()

        monitor.record_epoch(1, 0.5, 0.4, 0.3, 0.2, 0.001)
        monitor.record_epoch(2, 0.4, 0.3, 0.2, 0.1, 0.001)

        history = monitor.get_metrics_history()
        assert len(history) == 2
        assert 'epoch' in history[0]
        assert 'train_loss' in history[0]


class TestModelConfig:
    """模型配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ModelConfig()

        assert config.look_back == 24
        assert config.lstm_units == [50, 50]
        assert config.dropout_rate == 0.2
        assert config.dense_units == 25
        assert config.batch_size == 32
        assert config.epochs == 50

    def test_custom_config(self):
        """测试自定义配置"""
        config = ModelConfig(
            look_back=48,
            lstm_units=[100, 100],
            dropout_rate=0.3,
            xgb_n_estimators=200,
            batch_size=64
        )

        assert config.look_back == 48
        assert config.lstm_units == [100, 100]
        assert config.dropout_rate == 0.3
        assert config.xgb_n_estimators == 200
        assert config.batch_size == 64


class TestMeteorForecast:
    """气象预测模型测试"""

    @pytest.fixture
    def temp_model_path(self):
        """创建临时模型路径"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_time_series(self):
        """生成示例时间序列数据"""
        np.random.seed(42)
        t = np.linspace(0, 100, 500)
        data = np.sin(t * 0.1) * 10 + np.random.randn(500) * 2
        return data.tolist()

    def test_initialization(self, temp_model_path):
        """测试模型初始化"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)

        assert model is not None
        assert model.model_path == temp_model_path
        assert model.preprocessor is not None
        assert model.monitor is not None

    def test_initialization_with_config(self, temp_model_path):
        """测试带配置的模型初始化"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        config = ModelConfig(
            look_back=12,
            lstm_units=[64, 64],
            batch_size=32
        )
        model = MeteorForecast(model_path=temp_model_path, config=config)

        assert model.config.look_back == 12
        assert model.config.lstm_units == [64, 64]

    def test_prepare_data(self, temp_model_path, sample_time_series):
        """测试数据准备"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = np.array(sample_time_series).reshape(-1, 1)
        scaled_data = model.preprocessor.fit_transform(data)

        X, y = model.prepare_data(scaled_data)

        assert X.shape[0] == y.shape[0]
        assert X.shape[1] == model.config.look_back
        assert X.shape[2] == 1

    def test_prepare_data_custom_lookback(self, temp_model_path, sample_time_series):
        """测试自定义回看窗口的数据准备"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = np.array(sample_time_series).reshape(-1, 1)
        scaled_data = model.preprocessor.fit_transform(data)

        custom_lookback = 48
        X, y = model.prepare_data(scaled_data, look_back=custom_lookback)

        assert X.shape[1] == custom_lookback

    def test_model_save_load(self, temp_model_path, sample_time_series):
        """测试模型保存和加载"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = np.array(sample_time_series).reshape(-1, 1)
        scaled_data = model.preprocessor.fit_transform(data)
        X, y = model.prepare_data(scaled_data)

        if model.lstm_model is None:
            model.lstm_model = model._build_lstm_model((X.shape[1], X.shape[2]))
        if model.xgb_model is None:
            model.xgb_model = model._build_xgb_model()

        model._save_model('lstm')
        model._save_model('xgb')

        assert os.path.exists(os.path.join(temp_model_path, 'lstm_model.h5'))
        assert os.path.exists(os.path.join(temp_model_path, 'xgb_model.json'))

    def test_prediction(self, temp_model_path, sample_time_series):
        """测试预测功能"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = np.array(sample_time_series).reshape(-1, 1)
        scaled_data = model.preprocessor.fit_transform(data)
        X, y = model.prepare_data(scaled_data)

        if model.lstm_model is None:
            model.lstm_model = model._build_lstm_model((X.shape[1], X.shape[2]))
        if model.xgb_model is None:
            model.xgb_model = model._build_xgb_model()

        predictions = model.predict(sample_time_series[:100])

        assert isinstance(predictions, list)
        assert len(predictions) > 0

    def test_correction(self, temp_model_path, sample_time_series):
        """测试订正功能"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = np.array(sample_time_series).reshape(-1, 1)
        scaled_data = model.preprocessor.fit_transform(data)
        X, y = model.prepare_data(scaled_data)

        if model.lstm_model is None:
            model.lstm_model = model._build_lstm_model((X.shape[1], X.shape[2]))
        if model.xgb_model is None:
            model.xgb_model = model._build_xgb_model()

        forecast_data = sample_time_series[100:150]
        observed_data = [f + 2 for f in forecast_data]

        corrected = model.correct(forecast_data, observed_data)

        assert isinstance(corrected, list)
        assert len(corrected) == len(forecast_data)

    def test_evaluation(self, temp_model_path, sample_time_series):
        """测试模型评估"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = np.array(sample_time_series).reshape(-1, 1)
        scaled_data = model.preprocessor.fit_transform(data)
        X, y = model.prepare_data(scaled_data)

        if model.lstm_model is None:
            model.lstm_model = model._build_lstm_model((X.shape[1], X.shape[2]))
        if model.xgb_model is None:
            model.xgb_model = model._build_xgb_model()

        eval_result = model.evaluate(X, y)

        assert isinstance(eval_result, dict)
        assert 'mse' in eval_result
        assert 'rmse' in eval_result
        assert 'mae' in eval_result
        assert 'r2' in eval_result

    def test_risk_heatmap(self, temp_model_path, sample_time_series):
        """测试风险热力图生成"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        forecast_data = sample_time_series[100:120]

        risk_data = model.generate_risk_heatmap(forecast_data)

        assert isinstance(risk_data, list)
        assert len(risk_data) == len(forecast_data)
        assert all('index' in item for item in risk_data)
        assert all('value' in item for item in risk_data)
        assert all('risk_level' in item for item in risk_data)

    def test_wrf_ghr_data_loading(self, temp_model_path):
        """测试WRF和GHR数据加载"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)

        wrf_data = {'predictions': [1, 2, 3, 4, 5]}
        ghr_data = {'predictions': [1.5, 2.5, 3.5, 4.5, 5.5]}

        assert model.load_wrf_data(wrf_data) is True
        assert model.load_ghr_data(ghr_data) is True
        assert model.wrf_data == wrf_data
        assert model.ghr_data == ghr_data


class TestEdgeCases:
    """边界情况测试"""

    @pytest.fixture
    def temp_model_path(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_empty_data(self, temp_model_path):
        """测试空数据"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        predictions = model.predict([])

        assert predictions == []

    def test_single_point(self, temp_model_path):
        """测试单点数据"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = [10.0]

        predictions = model.predict(data)

        assert isinstance(predictions, list)

    def test_short_timeseries(self, temp_model_path):
        """测试短时间序列"""
        if not ENHANCED_MODEL_AVAILABLE:
            pytest.skip("增强模型不可用")

        model = MeteorForecast(model_path=temp_model_path)
        data = list(range(10))

        predictions = model.predict(data)

        assert isinstance(predictions, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

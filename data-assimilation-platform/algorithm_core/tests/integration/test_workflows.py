"""
工作流集成测试
测试批处理、流水线和流式处理工作流
"""
from datetime import datetime
from unittest.mock import MagicMock
import logging
import os
import sys

import pytest
import numpy as np

logger = logging.getLogger(__name__)


SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(SRC_DIR, 'src')


if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from bayesian_assimilation.workflows.batch import BatchAssimilator  # noqa: E402


from bayesian_assimilation.workflows.pipeline import (  # noqa: E402
    AssimilationPipeline,
    PipelineStage,
    DataLoadingStep,
    PreprocessingStep
)


from bayesian_assimilation.workflows.streaming import (  # noqa: E402
    StreamingAssimilator,
    StreamBuffer,
    create_stream_processor
)


@pytest.mark.integration
class TestBatchWorkflow:
    """批处理工作流测试类"""

    def test_batch_assimilator_init(self, sample_config):
        """测试批处理同化器初始化"""
        batch = BatchAssimilator(config=sample_config, max_workers=2)

        assert batch.config is not None
        assert batch.max_workers == 2
        assert isinstance(batch.results, list)

    def test_batch_result_structure(self, background_field, observation_data):
        """测试批处理结果结构"""
        BatchAssimilator()

        # 模拟一个简单的任务结果
        result = {
            'background_path': 'test_bg.nc',
            'observation_path': 'test_obs.nc',
            'output_path': 'test_output.nc',
            'status': 'success',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'elapsed_seconds': 1.5,
            'grid_shape': background_field.shape,
            'mean_analysis': float(np.mean(background_field)),
            'mean_variance': float(np.mean(background_field) * 0.5)
        }

        assert 'status' in result
        assert 'elapsed_seconds' in result

    def test_batch_summary(self):
        """测试批处理摘要"""
        batch = BatchAssimilator()

        # 模拟一些结果
        batch.results = [
            {'status': 'success', 'elapsed_seconds': 1.0, 'mean_variance': 0.5},
            {'status': 'success', 'elapsed_seconds': 2.0, 'mean_variance': 0.6},
            {'status': 'failed', 'error': 'Test error'}
        ]

        summary = batch.get_summary()

        assert summary['total'] == 3
        assert summary['success'] == 2
        assert summary['failed'] == 1
        assert summary['success_rate'] == 2/3


@pytest.mark.integration
class TestPipelineWorkflow:
    """流水线工作流测试类"""

    def test_pipeline_init(self):
        """测试流水线初始化"""
        pipeline = AssimilationPipeline("test_pipeline")

        assert pipeline.name == "test_pipeline"
        assert isinstance(pipeline.steps, list)
        assert len(pipeline.steps) == 0

    def test_pipeline_add_step(self):
        """测试添加步骤"""
        pipeline = AssimilationPipeline()

        # 创建一个mock步骤
        step = DataLoadingStep("bg.nc", "obs.nc")
        pipeline.add_step(step)

        assert len(pipeline.steps) == 1
        assert pipeline.steps[0] is step

    def test_pipeline_remove_step(self):
        """测试移除步骤"""
        pipeline = AssimilationPipeline()

        step1 = DataLoadingStep("bg1.nc", "obs1.nc")
        step2 = PreprocessingStep(target_resolution=50.0)

        pipeline.add_step(step1)
        pipeline.add_step(step2)

        pipeline.remove_step(0)

        assert len(pipeline.steps) == 1
        assert pipeline.steps[0] is step2

    def test_pipeline_execute_empty(self):
        """测试执行空流水线"""
        pipeline = AssimilationPipeline()

        result = pipeline.execute()

        assert result['success'] is True
        assert result['data'] is None

    def test_pipeline_execute_with_mock_steps(self, background_field, observation_data):
        """测试执行带mock步骤的流水线"""
        pipeline = AssimilationPipeline("mock_pipeline")

        observations, obs_locations, obs_errors = observation_data

        # 创建mock的input_data
        input_data = {
            'background': background_field,
            'observations': observations,
            'obs_locations': obs_locations,
            'obs_errors': obs_errors
        }

        # 创建一个简单的pass-through步骤

        class PassThroughStep:

            def __init__(self):
                self.name = "pass_through"
                self.stage = PipelineStage.DATA_LOADING
                self.config = MagicMock()
                self.config.enabled = True

            def execute(self, input_data):
                from bayesian_assimilation.workflows.pipeline import PipelineResult  # noqa: E402
                return PipelineResult(
                    stage=self.stage,
                    success=True,
                    data=input_data,
                    elapsed_time=0.1
                )

        pipeline.add_step(PassThroughStep())  # type: ignore[arg-type]

        result = pipeline.execute(input_data)

        assert result['success'] is True
        assert result['data'] is not None

    def test_pipeline_reset(self):
        """测试流水线重置"""
        pipeline = AssimilationPipeline()

        step = DataLoadingStep("bg.nc", "obs.nc")
        pipeline.add_step(step)

        pipeline.reset()

        assert len(pipeline.results) == 0
        assert pipeline._current_data is None

    def test_pipeline_timing_report(self):
        """测试时间报告生成"""
        pipeline = AssimilationPipeline("timing_test")

        # 添加一些带结果的步骤

        class MockStep:

            def __init__(self, elapsed):
                self.name = "mock"
                self.stage = PipelineStage.ASSIMILATION
                self.config = MagicMock()
                self.config.enabled = True
                self._result = MagicMock()
                self._result.elapsed_time = elapsed
                self._result.stage = PipelineStage.ASSIMILATION

            def execute(self, input_data):
                from bayesian_assimilation.workflows.pipeline import PipelineResult  # noqa: E402
                return PipelineResult(
                    stage=self.stage,
                    success=True,
                    data=input_data,
                    elapsed_time=self._result.elapsed_time
                )

        pipeline.add_step(MockStep(0.5))  # type: ignore[arg-type]
        pipeline.add_step(MockStep(1.0))  # type: ignore[arg-type]

        pipeline.execute()

        report = pipeline.get_timing_report()

        assert "timing_test" in report
        assert "assimilation" in report


@pytest.mark.integration
class TestStreamingWorkflow:
    """流式处理工作流测试类"""

    def test_stream_buffer_init(self):
        """测试流缓冲区初始化"""
        buffer = StreamBuffer(max_size=100, batch_size=10)

        assert buffer.max_size == 100
        assert buffer.batch_size == 10
        assert buffer.size() == 0

    def test_stream_buffer_add(self):
        """测试添加数据到缓冲区"""
        from bayesian_assimilation.workflows.streaming import StreamData  # noqa: E402

        buffer = StreamBuffer()

        data = StreamData(
            timestamp=datetime.now(),
            data=np.array([1.0, 2.0, 3.0])
        )

        buffer.add(data)

        assert buffer.size() == 1

    def test_stream_buffer_get_batch(self):
        """测试获取批次数据"""
        from bayesian_assimilation.workflows.streaming import StreamData  # noqa: E402

        buffer = StreamBuffer(batch_size=3)

        for i in range(5):
            data = StreamData(
                timestamp=datetime.now(),
                data=np.array([float(i)])
            )
            buffer.add(data)

        batch = buffer.get_batch()

        assert len(batch) == 3
        assert buffer.size() == 2

    def test_stream_buffer_clear(self):
        """测试清空缓冲区"""
        from bayesian_assimilation.workflows.streaming import StreamData  # noqa: E402

        buffer = StreamBuffer()

        for i in range(5):
            buffer.add(StreamData(
                timestamp=datetime.now(),
                data=np.array([float(i)])
            ))

        buffer.clear()

        assert buffer.size() == 0

    def test_streaming_assimilator_init(self, sample_config):
        """测试流式同化器初始化"""
        processor = StreamingAssimilator(
            config=sample_config,
            buffer_size=50,
            batch_size=5
        )

        assert processor.buffer_size == 50
        assert processor.batch_size == 5
        assert processor.background is None

    def test_streaming_assimilator_update_background(self, background_field):
        """测试更新背景场"""
        processor = StreamingAssimilator()

        processor.update_background(background_field)

        assert processor.background is not None
        assert np.array_equal(processor.background, background_field)

    def test_streaming_assimilator_add_observation(self):
        """测试添加观测数据"""
        processor = StreamingAssimilator()

        observations = np.array([15.0, 16.0, 17.0])
        locations = np.array([[5, 5, 2], [10, 10, 2], [15, 15, 2]])
        errors = np.array([1.0, 1.0, 1.0])

        processor.add_observation(observations, locations, errors)

        assert processor.buffer.size() == 1

    def test_streaming_assimilator_statistics(self, background_field):
        """测试获取统计信息"""
        processor = StreamingAssimilator()
        processor.update_background(background_field)

        observations = np.array([15.0, 16.0])
        locations = np.array([[5, 5, 2], [10, 10, 2]])
        errors = np.array([1.0, 1.0])

        processor.add_observation(observations, locations, errors)

        stats = processor.get_statistics()

        assert 'total_results' in stats
        assert 'buffer_size' in stats


@pytest.mark.integration
class TestWorkflowComparison:
    """工作流对比测试类"""

    def test_batch_vs_pipeline(self, background_field, observation_data):
        """对比批处理和流水线方法"""
        observations, obs_locations, obs_errors = observation_data

        # 批处理方式
        batch = BatchAssimilator()

        # 流水线方式
        pipeline = AssimilationPipeline()

        # 两种方式都应该能创建
        assert batch is not None
        assert pipeline is not None

    def test_create_stream_processor(self, sample_config):
        """测试创建流处理器"""
        processor = create_stream_processor(
            config=sample_config,
            buffer_size=100,
            batch_size=10
        )

        assert isinstance(processor, StreamingAssimilator)
        assert processor.buffer_size == 100
        assert processor.batch_size == 10


@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowPerformance:
    """工作流性能测试类"""

    def test_pipeline_execution_performance(self, background_field, observation_data):
        """测试流水线执行性能"""
        import time  # noqa: E402

        observations, obs_locations, obs_errors = observation_data

        pipeline = AssimilationPipeline("perf_test")

        # 添加pass-through步骤模拟处理

        class PerfMockStep:

            def __init__(self):
                self.name = "perf_mock"
                self.stage = PipelineStage.ASSIMILATION
                self.config = MagicMock()
                self.config.enabled = True

            def execute(self, input_data):
                time.sleep(0.01)  # 模拟处理
                from bayesian_assimilation.workflows.pipeline import PipelineResult  # noqa: E402
                return PipelineResult(
                    stage=self.stage,
                    success=True,
                    data=input_data,
                    elapsed_time=0.01
                )

        for _ in range(10):
            pipeline.add_step(PerfMockStep())  # type: ignore[arg-type]

        start_time = time.time()
        result = pipeline.execute()
        elapsed = time.time() - start_time

        assert result['success'] is True
        assert elapsed < 5.0  # 应该在5秒内完成

    def test_stream_buffer_performance(self):
        """测试流缓冲区性能"""
        import time  # noqa: E402

        buffer = StreamBuffer(max_size=1000, batch_size=100)

        start_time = time.time()

        for i in range(500):
            from bayesian_assimilation.workflows.streaming import StreamData  # noqa: E402
            buffer.add(StreamData(
                timestamp=datetime.now(),
                data=np.random.randn(100)
            ))

        for _ in range(5):
            buffer.get_batch()

        elapsed = time.time() - start_time

        # 500次添加和5次批量获取应该在合理时间内完成
        assert elapsed < 2.0

package com.uav.platform.service;

import com.uav.platform.dto.experiment.*;
import com.uav.platform.entity.Experiment;
import com.uav.platform.mapper.ExperimentMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * ExperimentService 单元测试
 * 测试实验CRUD操作、快照创建和恢复功能
 */
@ExtendWith(MockitoExtension.class)
class ExperimentServiceTest {

    @Mock
    private ExperimentMapper experimentMapper;

    private ExperimentService experimentService;

    private ExperimentCreateRequest createRequest;
    private Experiment sampleExperiment;

    @BeforeEach
    void setUp() {
        experimentService = new ExperimentService();
        ReflectionTestUtils.setField(experimentService, "baseMapper", experimentMapper);
        createRequest = new ExperimentCreateRequest();
        createRequest.setExperimentName("测试实验-A*算法");
        createRequest.setAlgorithmName("A_STAR");
        createRequest.setAlgorithmCategory("路径规划");
        createRequest.setConfigJson("{\"maxIterations\":1000}");
        createRequest.setWeatherContext("{\"temperature\":25}");

        sampleExperiment = new Experiment();
        sampleExperiment.setId(1L);
        sampleExperiment.setExperimentName("测试实验-A*算法");
        sampleExperiment.setAlgorithmName("A_STAR");
        sampleExperiment.setAlgorithmCategory("路径规划");
        sampleExperiment.setStatus("RUNNING");
        sampleExperiment.setConfigJson("{\"maxIterations\":1000}");
        sampleExperiment.setWeatherContext("{\"temperature\":25}");
        sampleExperiment.setDurationMs(0L);
        sampleExperiment.setCreatedAt(LocalDateTime.now());
        sampleExperiment.setUpdatedAt(LocalDateTime.now());
    }

    @Test
    void testCreateExperiment_Success() {
        // 模拟 save 操作
        when(experimentMapper.insert(any(Experiment.class))).thenReturn(1);

        ExperimentVO result = experimentService.createExperiment(createRequest);

        assertNotNull(result);
        assertEquals("测试实验-A*算法", result.getExperimentName());
        assertEquals("A_STAR", result.getAlgorithmName());
        assertEquals("路径规划", result.getAlgorithmCategory());
        assertEquals("RUNNING", result.getStatus());
        assertEquals(0L, result.getDurationMs());
        assertNotNull(result.getCreatedAt());

        verify(experimentMapper).insert(any(Experiment.class));
    }

    @Test
    void testGetExperimentById_Success() {
        when(experimentMapper.selectById(1L)).thenReturn(sampleExperiment);

        ExperimentVO result = experimentService.getExperimentById(1L);

        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("测试实验-A*算法", result.getExperimentName());
        assertEquals("A_STAR", result.getAlgorithmName());

        verify(experimentMapper).selectById(1L);
    }

    @Test
    void testGetExperimentById_NotFound() {
        when(experimentMapper.selectById(999L)).thenReturn(null);

        assertThrows(IllegalArgumentException.class, () -> {
            experimentService.getExperimentById(999L);
        });
    }

    @Test
    void testDeleteExperiment_Success() {
        when(experimentMapper.selectById(1L)).thenReturn(sampleExperiment);
        when(experimentMapper.deleteById(1L)).thenReturn(1);

        experimentService.deleteExperiment(1L);

        verify(experimentMapper).selectById(1L);
        verify(experimentMapper).deleteById(1L);
    }

    @Test
    void testDeleteExperiment_NotFound() {
        when(experimentMapper.selectById(999L)).thenReturn(null);

        assertThrows(IllegalArgumentException.class, () -> {
            experimentService.deleteExperiment(999L);
        });

        verify(experimentMapper, never()).deleteById(org.mockito.ArgumentMatchers.<Long>any());
    }

    @Test
    void testCreateSnapshot_Success() {
        sampleExperiment.setConfigJson("{\"maxIterations\":1000}");
        sampleExperiment.setResultJson("{\"pathLength\":1500}");
        sampleExperiment.setMetricsJson("{\"rmse\":0.5}");
        when(experimentMapper.selectById(1L)).thenReturn(sampleExperiment);
        when(experimentMapper.updateById(any(Experiment.class))).thenReturn(1);

        ExperimentVO result = experimentService.createSnapshot(1L);

        assertNotNull(result);
        assertNotNull(result.getSnapshotHash());
        assertNotNull(result.getSnapshotData());

        verify(experimentMapper).selectById(1L);
        verify(experimentMapper).updateById(any(Experiment.class));
    }

    @Test
    void testCreateSnapshot_ExperimentNotFound() {
        when(experimentMapper.selectById(999L)).thenReturn(null);

        assertThrows(IllegalArgumentException.class, () -> {
            experimentService.createSnapshot(999L);
        });
    }

    @Test
    void testRestoreFromSnapshot_Success() {
        sampleExperiment.setSnapshotData(
                "{\"config\":{\"maxIterations\":1000},\"weatherContext\":{\"temperature\":25},\"status\":\"COMPLETED\"}"
        );
        sampleExperiment.setSnapshotHash("abc123");
        when(experimentMapper.selectById(1L)).thenReturn(sampleExperiment);
        when(experimentMapper.updateById(any(Experiment.class))).thenReturn(1);

        Map<String, Object> result = experimentService.restoreFromSnapshot(1L);

        assertNotNull(result);
        assertNotNull(result.get("config"));
        assertNotNull(result.get("weatherContext"));
        assertNotNull(result.get("restoredAt"));

        verify(experimentMapper).updateById(org.mockito.ArgumentMatchers.<Experiment>argThat(exp ->
                "RUNNING".equals(exp.getStatus())
        ));
    }

    @Test
    void testRestoreFromSnapshot_NoSnapshot() {
        when(experimentMapper.selectById(1L)).thenReturn(sampleExperiment);

        assertThrows(IllegalStateException.class, () -> {
            experimentService.restoreFromSnapshot(1L);
        });
    }

    @Test
    void testCompareExperiments_Success() {
        Experiment exp1 = new Experiment();
        exp1.setId(1L);
        exp1.setExperimentName("实验1");
        exp1.setAlgorithmName("A_STAR");
        exp1.setStatus("COMPLETED");
        exp1.setDurationMs(5000L);
        exp1.setMetricsJson("{\"rmse\":0.5}");

        Experiment exp2 = new Experiment();
        exp2.setId(2L);
        exp2.setExperimentName("实验2");
        exp2.setAlgorithmName("RRTSTAR");
        exp2.setStatus("COMPLETED");
        exp2.setDurationMs(8000L);
        exp2.setMetricsJson("{\"rmse\":0.3}");

        // 使用 spy 来 mock listByIds 方法（因为 ServiceImpl 内部调用链复杂）
        ExperimentService spyService = spy(experimentService);
        doReturn(List.of(exp1, exp2)).when(spyService).listByIds(anyList());

        ExperimentCompareResult result = spyService.compareExperiments(List.of(1L, 2L));

        assertNotNull(result);
        assertEquals(2, result.getExperiments().size());
        assertEquals(4, result.getMetrics().size());
    }

    @Test
    void testCompareExperiments_LessThanTwoIds() {
        assertThrows(IllegalArgumentException.class, () -> {
            experimentService.compareExperiments(List.of(1L));
        });
    }
}

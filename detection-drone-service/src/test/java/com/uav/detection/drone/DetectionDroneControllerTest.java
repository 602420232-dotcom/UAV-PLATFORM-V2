package com.uav.detection.drone;

import com.uav.detection.drone.controller.DetectionDroneController;
import com.uav.detection.drone.model.*;
import com.uav.detection.drone.repository.DetectionMissionRepository;
import com.uav.detection.drone.repository.DetectionRouteRepository;
import com.uav.detection.drone.repository.DetectionSampleRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * 探测无人机服务单元测试
 */
@SuppressWarnings("null")
@ExtendWith(MockitoExtension.class)
class DetectionDroneControllerTest {

    @Mock
    private DetectionMissionRepository missionRepo;

    @Mock
    private DetectionRouteRepository routeRepo;

    @Mock
    private DetectionSampleRepository sampleRepo;

    private DetectionDroneController controller;

    private DetectionMission sampleMission;
    private DetectionRoute sampleRoute;
    private DetectionSample sampleSample;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        controller = new DetectionDroneController(missionRepo, routeRepo, sampleRepo);

        sampleMission = DetectionMission.builder()
                .id(1L)
                .missionName("测试任务")
                .missionType(MissionType.GRID_SCAN)
                .status(MissionStatus.CREATED)
                .droneId("UAV001")
                .droneName("测试无人机")
                .areaMinLon(120.0)
                .areaMinLat(30.0)
                .areaMaxLon(122.0)
                .areaMaxLat(32.0)
                .minAltitude(100.0)
                .maxAltitude(500.0)
                .gridResolution(0.01)
                .verticalLayers(5)
                .sampleCount(0)
                .createdAt(LocalDateTime.now())
                .build();

        sampleRoute = DetectionRoute.builder()
                .id(1L)
                .missionId(1L)
                .sequenceNum(1)
                .longitude(121.0)
                .latitude(31.0)
                .altitude(200.0)
                .speed(10.0)
                .hoverSeconds(5)
                .build();

        sampleSample = DetectionSample.builder()
                .id(1L)
                .missionId(1L)
                .droneId("UAV001")
                .sequenceNum(1)
                .sampleTime(LocalDateTime.now())
                .longitude(121.0)
                .latitude(31.0)
                .altitude(200.0)
                .temperature(25.0)
                .humidity(60.0)
                .pressure(1013.0)
                .windSpeed(3.0)
                .windDirection(90.0)
                .qualityFlag(1.0)
                .build();
    }

    @Test
    void createMission_WithValidData_ReturnsSuccess() {
        when(missionRepo.save(any(DetectionMission.class))).thenReturn(sampleMission);
        when(routeRepo.findByMissionIdOrderBySequenceNumAsc(anyLong())).thenReturn(List.of());

        Map<String, Object> request = Map.of(
                "missionName", "测试任务",
                "missionType", "GRID_SCAN",
                "droneId", "UAV001",
                "droneName", "测试无人机",
                "areaMinLon", 120.0,
                "areaMinLat", 30.0,
                "areaMaxLon", 122.0,
                "areaMaxLat", 32.0
        );

        ResponseEntity<Map<String, Object>> response = controller.createMission(request);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals("任务创建成功", result.get("message"));
        assertEquals(1L, result.get("missionId"));
        verify(missionRepo).save(any(DetectionMission.class));
    }

    @Test
    void listMissions_WithPagination_ReturnsPagedResults() {
        Page<DetectionMission> page = new PageImpl<>(List.of(sampleMission));
        when(missionRepo.findAllByOrderByCreatedAtDesc(any(PageRequest.class))).thenReturn(page);

        ResponseEntity<Map<String, Object>> response = controller.listMissions(1, 10, null);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals(1, ((List<?>) result.get("data")).size());
        assertEquals(1L, result.get("total"));
    }

    @Test
    void listMissions_WithStatusFilter_ReturnsFilteredResults() {
        when(missionRepo.findByStatus(MissionStatus.CREATED)).thenReturn(List.of(sampleMission));

        ResponseEntity<Map<String, Object>> response = controller.listMissions(1, 10, "CREATED");
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals(1, ((List<?>) result.get("data")).size());
    }

    @Test
    void getMissionStatus_WithValidId_ReturnsMissionAndRoutes() {
        when(missionRepo.findById(1L)).thenReturn(Optional.of(sampleMission));
        when(routeRepo.findByMissionIdOrderBySequenceNumAsc(1L)).thenReturn(List.of(sampleRoute));

        ResponseEntity<Map<String, Object>> response = controller.getMissionStatus(1L);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertNotNull(result.get("mission"));
        assertNotNull(result.get("route"));
    }

    @Test
    void getMissionStatus_WithInvalidId_ReturnsNotFound() {
        when(missionRepo.findById(999L)).thenReturn(Optional.empty());

        ResponseEntity<Map<String, Object>> response = controller.getMissionStatus(999L);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(false, result.get("success"));
        assertEquals("任务不存在: id=999", result.get("message"));
    }

    @Test
    void updateMissionStatus_ToInFlight_SetsActualStart() {
        when(missionRepo.findById(1L)).thenReturn(Optional.of(sampleMission));
        when(missionRepo.save(any(DetectionMission.class))).thenReturn(sampleMission);

        Map<String, Object> request = Map.of("status", "IN_FLIGHT");

        ResponseEntity<Map<String, Object>> response = controller.updateMissionStatus(1L, request);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        verify(missionRepo).save(any(DetectionMission.class));
    }

    @Test
    void updateMissionStatus_ToLanded_SetsActualEndAndOfflineFlag() {
        when(missionRepo.findById(1L)).thenReturn(Optional.of(sampleMission));
        when(missionRepo.save(any(DetectionMission.class))).thenReturn(sampleMission);

        Map<String, Object> request = Map.of("status", "LANDED");

        ResponseEntity<Map<String, Object>> response = controller.updateMissionStatus(1L, request);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        verify(missionRepo).save(any(DetectionMission.class));
    }

    @Test
    void uploadSample_SingleSample_ReturnsSuccess() {
        when(sampleRepo.findMaxSequenceNumByMissionId(1L)).thenReturn(0);
        when(sampleRepo.save(any(DetectionSample.class))).thenReturn(sampleSample);
        when(missionRepo.findById(1L)).thenReturn(Optional.of(sampleMission));
        when(missionRepo.save(any(DetectionMission.class))).thenReturn(sampleMission);

        Map<String, Object> request = Map.of(
                "missionId", 1L,
                "droneId", "UAV001",
                "longitude", 121.0,
                "latitude", 31.0,
                "altitude", 200.0,
                "temperature", 25.0
        );

        ResponseEntity<Map<String, Object>> response = controller.uploadSample(request);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals(1, result.get("uploadedCount"));
        verify(sampleRepo).save(any(DetectionSample.class));
    }

    @Test
    void uploadSample_BatchSamples_ReturnsSuccess() {
        when(sampleRepo.findMaxSequenceNumByMissionId(1L)).thenReturn(0);
        when(sampleRepo.save(any(DetectionSample.class))).thenReturn(sampleSample);
        when(missionRepo.findById(1L)).thenReturn(Optional.of(sampleMission));
        when(missionRepo.save(any(DetectionMission.class))).thenReturn(sampleMission);

        Map<String, Object> sample1 = Map.of(
                "missionId", 1L, "droneId", "UAV001",
                "longitude", 121.0, "latitude", 31.0,
                "temperature", 25.0
        );
        Map<String, Object> sample2 = Map.of(
                "missionId", 1L, "droneId", "UAV001",
                "longitude", 121.1, "latitude", 31.1,
                "temperature", 26.0
        );
        Map<String, Object> request = Map.of(
                "missionId", 1L,
                "samples", List.of(sample1, sample2)
        );

        ResponseEntity<Map<String, Object>> response = controller.uploadSample(request);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertEquals(2, result.get("uploadedCount"));
        verify(sampleRepo, times(2)).save(any(DetectionSample.class));
    }

    @Test
    void getMissionData_WithValidId_ReturnsMissionAndSamples() {
        Page<DetectionSample> samplePage = new PageImpl<>(List.of(sampleSample));
        when(missionRepo.findById(1L)).thenReturn(Optional.of(sampleMission));
        when(sampleRepo.findByMissionId(eq(1L), any(PageRequest.class))).thenReturn(samplePage);
        when(sampleRepo.getMissionStatistics(1L)).thenReturn(List.of());

        ResponseEntity<Map<String, Object>> response = controller.getMissionData(1L, 1, 100);
        Map<String, Object> result = response.getBody();
        assertNotNull(result);

        assertEquals(true, result.get("success"));
        assertNotNull(result.get("mission"));
        assertNotNull(result.get("data"));
    }
}

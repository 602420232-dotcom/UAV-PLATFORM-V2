package com.uav.service.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.model.Drone;
import com.uav.model.OperationLog;
import com.uav.model.PathPlan;
import com.uav.model.Task;
import com.uav.service.DroneService;
import com.uav.service.OperationLogService;
import com.uav.service.PathPlanService;
import com.uav.service.TaskService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaHandler;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * Kafka 消息消费者服务
 * 监听 uav-tasks、uav-drones、uav-path-plans 主题的消息
 */
@Service
@KafkaListener(topics = {"uav-tasks", "uav-drones", "uav-path-plans"}, groupId = "#{T(java.lang.String).valueOf('${spring.kafka.consumer.group-id:uav-path-planning-group}')}")
public class KafkaConsumerService {

    private static final Logger log = LoggerFactory.getLogger(KafkaConsumerService.class);

    private final ObjectMapper objectMapper;
    private final TaskService taskService;
    private final DroneService droneService;
    private final PathPlanService pathPlanService;
    private final OperationLogService operationLogService;

    public KafkaConsumerService(
            TaskService taskService,
            DroneService droneService,
            PathPlanService pathPlanService,
            OperationLogService operationLogService) {
        this.objectMapper = new ObjectMapper();
        this.taskService = taskService;
        this.droneService = droneService;
        this.pathPlanService = pathPlanService;
        this.operationLogService = operationLogService;
    }

    @KafkaHandler
    public void consumeMessage(String message) {
        log.info("Received Kafka message: {}", message);

        try {
            JsonNode jsonNode = objectMapper.readTree(message);
            String eventType = jsonNode.has("eventType") ? jsonNode.get("eventType").asText() : "UNKNOWN";

            switch (eventType) {
                case "TASK_UPDATE":
                    processTaskEvent(jsonNode);
                    break;
                case "DRONE_UPDATE":
                    processDroneEvent(jsonNode);
                    break;
                case "PATH_PLAN_UPDATE":
                    processPathPlanEvent(jsonNode);
                    break;
                default:
                    log.warn("Unknown event type: {}", eventType);
                    break;
            }
        } catch (JsonProcessingException e) {
            log.error("Failed to parse Kafka message JSON: {}, error: {}", message, e.getMessage());
        } catch (Exception e) {
            log.error("Error processing Kafka message: {}", e.getMessage(), e);
        }
    }

    private void processTaskEvent(JsonNode jsonNode) {
        Long taskId = jsonNode.has("taskId") ? jsonNode.get("taskId").asLong() : null;
        String status = jsonNode.has("status") ? jsonNode.get("status").asText() : null;
        String name = jsonNode.has("name") ? jsonNode.get("name").asText() : null;

        log.info("Processing task event: taskId={}, name='{}', status={}", taskId, name, status);

        if (taskId == null || status == null) {
            log.warn("Invalid task event: missing taskId or status");
            return;
        }

        try {
            Task task = taskService.findById(taskId);
            String oldStatus = task.getStatus();
            task.setStatus(status);

            if ("COMPLETED".equals(status)) {
                log.info("Task {} completed successfully", taskId);
                task.setEndTime(LocalDateTime.now());
                operationLogService.create(createLog("TASK_COMPLETED",
                    "Task '" + task.getName() + "' (ID: " + taskId + ") completed successfully"));
            } else if ("FAILED".equals(status)) {
                log.error("Task {} failed", taskId);
                operationLogService.create(createLog("TASK_FAILED",
                    "Task '" + task.getName() + "' (ID: " + taskId + ") failed"));
            } else if ("IN_PROGRESS".equals(status) && !"IN_PROGRESS".equals(oldStatus)) {
                log.info("Task {} started", taskId);
                operationLogService.create(createLog("TASK_STARTED",
                    "Task '" + task.getName() + "' (ID: " + taskId + ") started execution"));
            }

            taskService.update(taskId, task);
            log.info("Task status updated successfully: taskId={}, oldStatus={}, newStatus={}",
                    taskId, oldStatus, status);

        } catch (Exception e) {
            log.error("Failed to update task status: taskId={}, error={}", taskId, e.getMessage());
        }
    }

    private void processDroneEvent(JsonNode jsonNode) {
        Long droneId = jsonNode.has("droneId") ? jsonNode.get("droneId").asLong() : null;
        String status = jsonNode.has("status") ? jsonNode.get("status").asText() : null;
        String model = jsonNode.has("model") ? jsonNode.get("model").asText() : null;
        int batteryLevel = jsonNode.has("batteryLevel") ? jsonNode.get("batteryLevel").asInt() : 0;

        log.info("Processing drone event: droneId={}, model='{}', status={}, battery={}%",
                droneId, model, status, batteryLevel);

        if (droneId == null) {
            log.warn("Invalid drone event: missing droneId");
            return;
        }

        try {
            Drone drone = droneService.findById(droneId);
            String oldStatus = drone.getStatus();
            drone.setStatus(status != null ? status : oldStatus);
            drone.setBatteryLevel(batteryLevel);

            if ("MAINTENANCE".equals(status) && !"MAINTENANCE".equals(oldStatus)) {
                log.warn("Drone {} entered maintenance mode", droneId);
                operationLogService.create(createLog("DRONE_MAINTENANCE",
                    "Drone '" + drone.getName() + "' (ID: " + droneId + ") entered maintenance mode"));
            } else if ("FAILED".equals(status) && !"FAILED".equals(oldStatus)) {
                log.error("Drone {} failed", droneId);
                operationLogService.create(createLog("DRONE_FAILED",
                    "Drone '" + drone.getName() + "' (ID: " + droneId + ") reported failure"));
            }

            if (batteryLevel < 20) {
                log.warn("Drone {} battery critically low: {}%", droneId, batteryLevel);
                operationLogService.create(createLog("DRONE_BATTERY_LOW",
                    "Drone '" + drone.getName() + "' (ID: " + droneId + ") battery critically low: " + batteryLevel + "%"));
            } else if (batteryLevel < 30) {
                log.warn("Drone {} battery low: {}%", droneId, batteryLevel);
            }

            droneService.update(droneId, drone);
            log.info("Drone status updated successfully: droneId={}, battery={}%", droneId, batteryLevel);

        } catch (Exception e) {
            log.error("Failed to update drone status: droneId={}, error={}", droneId, e.getMessage());
        }
    }

    private void processPathPlanEvent(JsonNode jsonNode) {
        Long planId = jsonNode.has("planId") ? jsonNode.get("planId").asLong() : null;
        String status = jsonNode.has("status") ? jsonNode.get("status").asText() : null;
        double totalDistance = jsonNode.has("totalDistance") ? jsonNode.get("totalDistance").asDouble() : 0.0;
        double totalRisk = jsonNode.has("totalRisk") ? jsonNode.get("totalRisk").asDouble() : 0.0;

        log.info("Processing path plan event: planId={}, status={}, distance={}m, risk={}",
                planId, status, totalDistance, totalRisk);

        if (planId == null) {
            log.warn("Invalid path plan event: missing planId");
            return;
        }

        try {
            PathPlan plan = pathPlanService.findById(planId);
            if (plan == null) {
                log.warn("Path plan not found: planId={}", planId);
                return;
            }

            String oldStatus = plan.getStatus();
            plan.setStatus(status != null ? status : oldStatus);
            plan.setTotalDistance(totalDistance);
            plan.setTotalRisk(totalRisk);

            if (totalRisk > 5.0) {
                log.warn("Path plan {} has high risk: {}", planId, totalRisk);
                operationLogService.create(createLog("PATH_PLAN_HIGH_RISK",
                    "Path plan (ID: " + planId + ") has high risk level: " + String.format("%.2f", totalRisk)));
            }

            if ("COMPLETED".equals(status) && !"COMPLETED".equals(oldStatus)) {
                log.info("Path plan {} completed successfully", planId);
                operationLogService.create(createLog("PATH_PLAN_COMPLETED",
                    "Path plan (ID: " + planId + ") completed. Total distance: " +
                    String.format("%.2f", totalDistance) + "m, Risk: " + String.format("%.2f", totalRisk)));
            } else if ("FAILED".equals(status) && !"FAILED".equals(oldStatus)) {
                log.error("Path plan {} failed", planId);
                operationLogService.create(createLog("PATH_PLAN_FAILED",
                    "Path plan (ID: " + planId + ") failed"));
            }

            pathPlanService.update(planId, plan);
            log.info("Path plan status updated successfully: planId={}, risk={}", planId, totalRisk);

        } catch (Exception e) {
            log.error("Failed to update path plan status: planId={}, error={}", planId, e.getMessage());
        }
    }

    private OperationLog createLog(String operation, String description) {
        OperationLog log = new OperationLog();
        log.setUsername("system");
        log.setOperation(operation);
        log.setDetails(description);
        return log;
    }
}

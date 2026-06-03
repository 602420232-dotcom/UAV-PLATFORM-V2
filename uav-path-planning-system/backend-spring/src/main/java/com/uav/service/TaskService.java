package com.uav.service;

import com.uav.model.Task;
import com.uav.repository.TaskRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TaskService {

    private final TaskRepository taskRepository;

    public TaskService(TaskRepository taskRepository) {
        this.taskRepository = taskRepository;
    }

    public List<Task> findAll() {
        return taskRepository.findAll();
    }

    public Task findById(Long id) {
        return taskRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Task not found with id: " + id));
    }

    public Task create(Task task) {
        return taskRepository.save(task);
    }

    public Task update(Long id, Task task) {
        Task existing = findById(id);
        existing.setName(task.getName());
        existing.setDescription(task.getDescription());
        existing.setLatitude(task.getLatitude());
        existing.setLongitude(task.getLongitude());
        existing.setAltitude(task.getAltitude());
        existing.setDemand(task.getDemand());
        existing.setStartTime(task.getStartTime());
        existing.setEndTime(task.getEndTime());
        existing.setServiceTime(task.getServiceTime());
        existing.setPriority(task.getPriority());
        existing.setStatus(task.getStatus());
        return taskRepository.save(existing);
    }

    public void delete(Long id) {
        Task existing = findById(id);
        taskRepository.delete(existing);
    }

    public List<Task> findByStatus(String status) {
        return taskRepository.findByStatus(status);
    }
}

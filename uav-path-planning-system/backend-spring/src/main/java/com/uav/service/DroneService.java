package com.uav.service;

import com.uav.model.Drone;
import com.uav.repository.DroneRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DroneService {

    private final DroneRepository droneRepository;

    public DroneService(DroneRepository droneRepository) {
        this.droneRepository = droneRepository;
    }

    public List<Drone> findAll() {
        return droneRepository.findAll();
    }

    public Drone findById(Long id) {
        return droneRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Drone not found with id: " + id));
    }

    public Drone create(Drone drone) {
        return droneRepository.save(drone);
    }

    public Drone update(Long id, Drone drone) {
        Drone existing = findById(id);
        existing.setName(drone.getName());
        existing.setModel(drone.getModel());
        existing.setSerialNumber(drone.getSerialNumber());
        existing.setMaxSpeed(drone.getMaxSpeed());
        existing.setMaxCapacity(drone.getMaxCapacity());
        existing.setMaxBattery(drone.getMaxBattery());
        existing.setCruiseSpeed(drone.getCruiseSpeed());
        existing.setWindResistance(drone.getWindResistance());
        existing.setStatus(drone.getStatus());
        existing.setCurrentLatitude(drone.getCurrentLatitude());
        existing.setCurrentLongitude(drone.getCurrentLongitude());
        existing.setCurrentAltitude(drone.getCurrentAltitude());
        existing.setBatteryLevel(drone.getBatteryLevel());
        return droneRepository.save(existing);
    }

    public void delete(Long id) {
        Drone existing = findById(id);
        droneRepository.delete(existing);
    }

    public List<Drone> findByStatus(String status) {
        return droneRepository.findByStatus(status);
    }
}

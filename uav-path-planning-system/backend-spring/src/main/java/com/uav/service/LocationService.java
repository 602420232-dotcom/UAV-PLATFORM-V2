package com.uav.service;

import com.uav.model.Location;
import com.uav.repository.LocationRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class LocationService {

    private final LocationRepository locationRepository;

    public LocationService(LocationRepository locationRepository) {
        this.locationRepository = locationRepository;
    }

    public List<Location> findAll() {
        return locationRepository.findAll();
    }

    public Location findById(Long id) {
        return locationRepository.findById(id).orElse(null);
    }

    public Location create(Location location) {
        return locationRepository.save(location);
    }

    public Location update(Long id, Location location) {
        Location existing = locationRepository.findById(id).orElse(null);
        if (existing == null) {
            return null;
        }
        existing.setName(location.getName());
        existing.setDescription(location.getDescription());
        existing.setLatitude(location.getLatitude());
        existing.setLongitude(location.getLongitude());
        existing.setAltitude(location.getAltitude());
        existing.setType(location.getType());
        existing.setRadius(location.getRadius());
        existing.setStatus(location.getStatus());
        return locationRepository.save(existing);
    }

    public void delete(Long id) {
        locationRepository.deleteById(id);
    }

    public List<Location> findByType(String type) {
        return locationRepository.findByType(type);
    }

    public Location findByName(String name) {
        return locationRepository.findByName(name);
    }
}

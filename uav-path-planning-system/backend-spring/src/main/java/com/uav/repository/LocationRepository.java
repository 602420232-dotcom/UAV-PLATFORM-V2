package com.uav.repository;

import com.uav.model.Location;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LocationRepository extends JpaRepository<Location, Long> {

    List<Location> findByType(String type);

    Location findByName(String name);

    List<Location> findByStatus(String status);
}

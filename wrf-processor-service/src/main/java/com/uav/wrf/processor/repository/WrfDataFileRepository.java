package com.uav.wrf.processor.repository;

import com.uav.wrf.processor.entity.WrfDataFile;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface WrfDataFileRepository extends JpaRepository<WrfDataFile, Long> {
    Optional<WrfDataFile> findByFileId(String fileId);
    Page<WrfDataFile> findAllByOrderByCreatedAtDesc(Pageable pageable);
    boolean existsByFileId(String fileId);
}

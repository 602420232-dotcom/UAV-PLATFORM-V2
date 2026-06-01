package com.uav.repository;

import com.uav.entity.TokenBlacklist;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface TokenBlacklistRepository extends JpaRepository<TokenBlacklist, Long> {

    Optional<TokenBlacklist> findByTokenId(String tokenId);

    boolean existsByTokenId(String tokenId);

    List<TokenBlacklist> findByUserId(Long userId);

    List<TokenBlacklist> findByExpiresAtBefore(LocalDateTime now);

    void deleteByExpiresAtBefore(LocalDateTime now);
}

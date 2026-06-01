package com.uav.repository;

import com.uav.entity.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {

    Optional<RefreshToken> findByRefreshTokenId(String refreshTokenId);

    boolean existsByRefreshTokenId(String refreshTokenId);

    List<RefreshToken> findByUserId(Long userId);

    List<RefreshToken> findByUserIdAndIsRevokedFalseAndIsUsedFalse(Long userId);

    List<RefreshToken> findByExpiresAtBefore(LocalDateTime now);

    void deleteByExpiresAtBefore(LocalDateTime now);
}

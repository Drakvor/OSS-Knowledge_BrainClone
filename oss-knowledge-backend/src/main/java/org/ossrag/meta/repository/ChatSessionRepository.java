package org.ossrag.meta.repository;

import org.ossrag.meta.domain.ChatSession;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ChatSessionRepository extends JpaRepository<ChatSession, UUID> {
    List<ChatSession> findByUserId(Long userId);
    Page<ChatSession> findByUserId(Long userId, Pageable pageable);
    List<ChatSession> findByUserIdAndStatus(Long userId, String status);
    Page<ChatSession> findByUserIdAndStatus(Long userId, String status, Pageable pageable);
    
    @Query("SELECT cs FROM ChatSession cs WHERE cs.deletedAt IS NULL")
    List<ChatSession> findAllActive();
    
    @Query("SELECT cs FROM ChatSession cs WHERE cs.userId = :userId AND cs.deletedAt IS NULL")
    List<ChatSession> findActiveByUserId(@Param("userId") Long userId);
    
    @Query("SELECT cs FROM ChatSession cs WHERE cs.status = 'active' AND cs.deletedAt IS NULL")
    Page<ChatSession> findActiveSessions(Pageable pageable);
    
    @Query("SELECT cs FROM ChatSession cs WHERE cs.userId = :userId AND cs.status = 'active' AND cs.deletedAt IS NULL")
    Page<ChatSession> findActiveByUserId(@Param("userId") Long userId, Pageable pageable);
}

package org.ossrag.meta.repository;

import org.ossrag.meta.domain.ChatMessage;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ChatMessageRepository extends JpaRepository<ChatMessage, UUID> {
    List<ChatMessage> findBySessionId(UUID sessionId);
    Page<ChatMessage> findBySessionId(UUID sessionId, Pageable pageable);
    List<ChatMessage> findBySessionIdOrderByCreatedAtAsc(UUID sessionId);
    List<ChatMessage> findByMessageType(String messageType);
    List<ChatMessage> findByParentMessageId(UUID parentMessageId);
    
    @Query("SELECT cm FROM ChatMessage cm WHERE cm.sessionId = :sessionId AND cm.deletedAt IS NULL ORDER BY cm.createdAt ASC")
    List<ChatMessage> findActiveBySessionIdOrderByCreatedAtAsc(@Param("sessionId") UUID sessionId);
    
    @Query("SELECT cm FROM ChatMessage cm WHERE cm.sessionId = :sessionId AND cm.deletedAt IS NULL")
    Page<ChatMessage> findActiveBySessionId(@Param("sessionId") UUID sessionId, Pageable pageable);
    
    // 토큰 기반 슬라이딩 윈도우를 위한 쿼리
    @Query(value = "SELECT * FROM chat_messages WHERE session_id = :sessionId AND deleted_at IS NULL ORDER BY created_at DESC LIMIT :limit", nativeQuery = true)
    List<ChatMessage> findRecentBySessionId(@Param("sessionId") UUID sessionId, @Param("limit") int limit);
    
    // 특정 토큰 수 이하로 최근 메시지들 가져오기 (슬라이딩 윈도우용)
    @Query(value = """
        WITH recent_messages AS (
            SELECT *, SUM(token_count) OVER (ORDER BY created_at DESC) as running_total
            FROM chat_messages 
            WHERE session_id = :sessionId AND deleted_at IS NULL
        )
        SELECT * FROM recent_messages 
        WHERE running_total <= :maxTokens 
        ORDER BY created_at DESC
        """, nativeQuery = true)
    List<ChatMessage> findRecentByTokenLimit(@Param("sessionId") UUID sessionId, @Param("maxTokens") int maxTokens);
    
    // 세션 내 최대 turn_index 조회 (새 메시지의 turn_index 설정용)
    @Query("SELECT MAX(cm.turnIndex) FROM ChatMessage cm WHERE cm.sessionId = :sessionId AND cm.deletedAt IS NULL")
    Integer findMaxTurnIndexBySessionId(@Param("sessionId") UUID sessionId);
    
    // turn_index 기반 슬라이딩 윈도우 (성능 최적화)
    @Query("SELECT cm FROM ChatMessage cm WHERE cm.sessionId = :sessionId AND cm.turnIndex > :minTurnIndex AND cm.deletedAt IS NULL ORDER BY cm.turnIndex ASC")
    List<ChatMessage> findBySessionIdAndTurnIndexGreaterThan(@Param("sessionId") UUID sessionId, @Param("minTurnIndex") Integer minTurnIndex);
    
    // department_id 관련 메서드들
    List<ChatMessage> findByDepartmentId(Long departmentId);
    List<ChatMessage> findByDepartmentIdAndSessionId(Long departmentId, UUID sessionId);
    List<ChatMessage> findByDepartmentIdAndMessageType(Long departmentId, String messageType);
    
    @Query("SELECT cm FROM ChatMessage cm WHERE cm.departmentId = :departmentId AND cm.deletedAt IS NULL ORDER BY cm.createdAt DESC")
    List<ChatMessage> findActiveByDepartmentId(@Param("departmentId") Long departmentId);
}

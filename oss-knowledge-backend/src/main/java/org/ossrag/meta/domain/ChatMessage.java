package org.ossrag.meta.domain;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * 채팅 메시지 엔터티
 */
@Entity
@Table(name = "chat_messages")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessage {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @JdbcTypeCode(SqlTypes.UUID)
    private UUID id;
    
    @Column(name = "session_id", nullable = false)
    @JdbcTypeCode(SqlTypes.UUID)
    private UUID sessionId;
    
    @Column(name = "turn_index", nullable = false)
    private Integer turnIndex; // 세션 내 메시지 순서 번호 (슬라이딩 윈도우 핵심)
    
    @Column(name = "message_type", nullable = false)
    private String messageType; // 'user', 'assistant', 'system'
    
    @Column(nullable = false, columnDefinition = "text")
    private String content;
    
    @Column(name = "token_count")
    private Integer tokenCount = 0;
    
    @Column(name = "department_id")
    private Long departmentId; // 메시지별 부서 컨텍스트
    
    @Column(name = "status")
    private String status; // 'pending', 'completed', 'failed'
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;
    
    @Column(name = "parent_message_id")
    @JdbcTypeCode(SqlTypes.UUID)
    private UUID parentMessageId;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;
    
    @Column(name = "deleted_at")
    private Instant deletedAt;

}

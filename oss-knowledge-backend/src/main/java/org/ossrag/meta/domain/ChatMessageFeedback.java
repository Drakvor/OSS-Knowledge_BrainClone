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
 * 채팅 메시지 피드백 엔터티
 */
@Entity
@Table(name = "chat_message_feedback")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessageFeedback {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @JdbcTypeCode(SqlTypes.UUID)
    private UUID id;
    
    @Column(name = "user_message_id", nullable = false)
    @JdbcTypeCode(SqlTypes.UUID)
    private UUID userMessageId;
    
    @Column(name = "user_id")
    private Long userId;
    
    @Column(nullable = false)
    private Integer rating; // 1-5점 별점
    
    private String comment;
    
    @Column(name = "feedback_type", nullable = false)
    private String feedbackType; // 'general', 'accuracy', 'helpfulness', 'clarity'
    
    @Column(name = "is_anonymous", nullable = false)
    private Boolean isAnonymous;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;
    
    @Column(name = "deleted_at")
    private Instant deletedAt;

}

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
 * 채팅 세션 엔터티
 */
@Entity
@Table(name = "chat_sessions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatSession {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @JdbcTypeCode(SqlTypes.UUID)
    private UUID id;
    
    @Column(name = "user_id")
    private Long userId;
    
    @Column(nullable = false)
    private String title;
    
    @Column(name = "llm_model", nullable = false)
    private String llmModel;
    
    @Column(nullable = false)
    private String status;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;
    
    @Column(name = "assistant_message_count", nullable = false)
    private Integer assistantMessageCount = 0;
    
    @Column(name = "total_message_count", nullable = false)
    private Integer totalMessageCount = 0;
    
    @Column(name = "total_tokens_used")
    private Long totalTokensUsed = 0L;
    
    @Column(name = "context_summary")
    private String contextSummary;
    
    @Column(name = "summary_updated_at")
    private Instant summaryUpdatedAt;
    
    @Column(name = "summary_version")
    private Integer summaryVersion = 1;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;
    
    @Column(name = "deleted_at")
    private Instant deletedAt;

}

package org.ossrag.meta.repository;

import org.ossrag.meta.domain.ChatMessageFeedback;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ChatMessageFeedbackRepository extends JpaRepository<ChatMessageFeedback, UUID> {
    List<ChatMessageFeedback> findByUserMessageId(UUID userMessageId);
    List<ChatMessageFeedback> findByUserId(Long userId);
    List<ChatMessageFeedback> findByRating(Integer rating);
    List<ChatMessageFeedback> findByFeedbackType(String feedbackType);
    List<ChatMessageFeedback> findByIsAnonymous(Boolean isAnonymous);
    
    @Query("SELECT cmf FROM ChatMessageFeedback cmf WHERE cmf.userMessageId = :userMessageId AND cmf.deletedAt IS NULL")
    List<ChatMessageFeedback> findActiveByUserMessageId(@Param("userMessageId") UUID userMessageId);
    
    @Query("SELECT AVG(cmf.rating) FROM ChatMessageFeedback cmf WHERE cmf.userMessageId = :userMessageId AND cmf.deletedAt IS NULL")
    Double findAverageRatingByUserMessageId(@Param("userMessageId") UUID userMessageId);
    
    @Query("SELECT COUNT(cmf) FROM ChatMessageFeedback cmf WHERE cmf.userMessageId = :userMessageId AND cmf.deletedAt IS NULL")
    Long countByUserMessageId(@Param("userMessageId") UUID userMessageId);
}

package org.ossrag.meta.service;

import org.ossrag.meta.domain.ChatMessageFeedback;
import org.ossrag.meta.dto.PageResponse;
import org.ossrag.meta.repository.ChatMessageFeedbackRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.UUID;

@Service
public class ChatMessageFeedbackService {
    private final ChatMessageFeedbackRepository repository;

    public ChatMessageFeedbackService(ChatMessageFeedbackRepository repository) {
        this.repository = repository;
    }

    // 기본 CRUD 메서드들
    public PageResponse<ChatMessageFeedback> list(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<ChatMessageFeedback> feedbackPage = repository.findAll(pageable);
        
        return new PageResponse<>(feedbackPage.getTotalElements(), page, size, feedbackPage.getContent());
    }

    public ChatMessageFeedback get(String id) {
        return repository.findById(UUID.fromString(id))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Chat message feedback not found"));
    }

    public ChatMessageFeedback create(ChatMessageFeedback feedback) {
        // 기본값 설정
        if (feedback.getFeedbackType() == null) {
            feedback.setFeedbackType("general");
        }
        if (feedback.getIsAnonymous() == null) {
            feedback.setIsAnonymous(true);
        }
        if (feedback.getMetadata() == null) {
            feedback.setMetadata(new java.util.HashMap<>());
        }

        return repository.save(feedback);
    }

    public ChatMessageFeedback update(ChatMessageFeedback feedback) {
        ChatMessageFeedback existing = get(feedback.getId().toString());
        
        // 업데이트 가능한 필드들만 설정
        if (feedback.getRating() != null) {
            existing.setRating(feedback.getRating());
        }
        if (feedback.getComment() != null) {
            existing.setComment(feedback.getComment());
        }
        if (feedback.getFeedbackType() != null) {
            existing.setFeedbackType(feedback.getFeedbackType());
        }
        if (feedback.getMetadata() != null) {
            existing.setMetadata(feedback.getMetadata());
        }

        return repository.save(existing);
    }

    public boolean delete(String id) {
        if (repository.existsById(UUID.fromString(id))) {
            repository.deleteById(UUID.fromString(id));
            return true;
        }
        return false;
    }

    // 특별한 메서드들
    public List<ChatMessageFeedback> findByUserMessageId(String userMessageId) {
        return repository.findActiveByUserMessageId(UUID.fromString(userMessageId));
    }

    public List<ChatMessageFeedback> findByUserId(Long userId, int page, int size) {
        return repository.findByUserId(userId);
    }

    public List<ChatMessageFeedback> findByRating(Integer rating, int page, int size) {
        return repository.findByRating(rating);
    }

    public List<ChatMessageFeedback> findByFeedbackType(String feedbackType, int page, int size) {
        return repository.findByFeedbackType(feedbackType);
    }

    public List<ChatMessageFeedback> findAnonymousFeedbacks(int page, int size) {
        return repository.findByIsAnonymous(true);
    }

    // 통계 메서드들
    public double getAverageRatingByUserMessageId(String userMessageId) {
        Double average = repository.findAverageRatingByUserMessageId(UUID.fromString(userMessageId));
        return average != null ? average : 0.0;
    }

    public long countByUserMessageId(String userMessageId) {
        Long count = repository.countByUserMessageId(UUID.fromString(userMessageId));
        return count != null ? count : 0L;
    }

    public long countByRating(Integer rating) {
        return repository.findByRating(rating).size();
    }

    // 편의 메서드들
    public List<ChatMessageFeedback> getPositiveFeedbacks(int page, int size) {
        return findByRating(5, page, size);
    }

    public List<ChatMessageFeedback> getNegativeFeedbacks(int page, int size) {
        return findByRating(1, page, size);
    }

    public List<ChatMessageFeedback> getGeneralFeedbacks(int page, int size) {
        return findByFeedbackType("general", page, size);
    }

    public List<ChatMessageFeedback> getAccuracyFeedbacks(int page, int size) {
        return findByFeedbackType("accuracy", page, size);
    }

    public List<ChatMessageFeedback> getHelpfulnessFeedbacks(int page, int size) {
        return findByFeedbackType("helpfulness", page, size);
    }

    public List<ChatMessageFeedback> getClarityFeedbacks(int page, int size) {
        return findByFeedbackType("clarity", page, size);
    }
}

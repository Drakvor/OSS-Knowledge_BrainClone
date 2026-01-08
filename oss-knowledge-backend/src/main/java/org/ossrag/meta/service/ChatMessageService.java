package org.ossrag.meta.service;

import org.ossrag.meta.domain.ChatMessage;
import org.ossrag.meta.dto.PageResponse;
import org.ossrag.meta.repository.ChatMessageRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.UUID;

@Service
public class ChatMessageService {
    private final ChatMessageRepository repository;
    private final ChatSessionService chatSessionService;

    public ChatMessageService(ChatMessageRepository repository, ChatSessionService chatSessionService) {
        this.repository = repository;
        this.chatSessionService = chatSessionService;
    }

    // 기본 CRUD 메서드들
    public PageResponse<ChatMessage> list(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<ChatMessage> messagePage = repository.findAll(pageable);
        
        return new PageResponse<>(messagePage.getTotalElements(), page, size, messagePage.getContent());
    }

    public ChatMessage get(String id) {
        return repository.findById(UUID.fromString(id))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Chat message not found"));
    }

    public ChatMessage create(ChatMessage chatMessage) {
        // 토큰 수는 다른 백엔드에서 계산해서 전달받음
        // chatMessage.getTokenCount()에 이미 값이 들어있음
        
        // turn_index 자동 설정 (세션 내 메시지 순서)
        Integer nextTurnIndex = repository.findMaxTurnIndexBySessionId(chatMessage.getSessionId());
        chatMessage.setTurnIndex(nextTurnIndex != null ? nextTurnIndex + 1 : 1);
        
        ChatMessage savedMessage = repository.save(chatMessage);
        
        // 메시지 생성 시 해당 채팅방의 메시지 카운트와 토큰 수 업데이트
        // 이렇게 하면 채팅방이 최상단으로 올라가고 슬라이딩 윈도우도 관리 가능
        chatSessionService.updateMessageCount(chatMessage.getSessionId(), chatMessage.getMessageType(), chatMessage.getTokenCount());
        
        return savedMessage;
    }

    public ChatMessage update(ChatMessage chatMessage) {
        ChatMessage existing = repository.findById(chatMessage.getId())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Chat message not found"));
        
        // 업데이트 가능한 필드들만 설정
        if (chatMessage.getContent() != null) {
            existing.setContent(chatMessage.getContent());
        }
        if (chatMessage.getMetadata() != null) {
            existing.setMetadata(chatMessage.getMetadata());
        }
        if (chatMessage.getParentMessageId() != null) {
            existing.setParentMessageId(chatMessage.getParentMessageId());
        }
        if (chatMessage.getStatus() != null) {
            existing.setStatus(chatMessage.getStatus());
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
    public List<ChatMessage> findBySessionId(String sessionId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return repository.findActiveBySessionId(UUID.fromString(sessionId), pageable).getContent();
    }

    public List<ChatMessage> findBySessionIdOrderByCreatedAt(String sessionId) {
        return repository.findActiveBySessionIdOrderByCreatedAtAsc(UUID.fromString(sessionId));
    }

    public List<ChatMessage> findByMessageType(String messageType, int page, int size) {
        return repository.findByMessageType(messageType);
    }

    public List<ChatMessage> findByParentMessageId(String parentMessageId) {
        return repository.findByParentMessageId(UUID.fromString(parentMessageId));
    }

    public boolean deleteBySessionId(String sessionId) {
        List<ChatMessage> messages = repository.findBySessionId(UUID.fromString(sessionId));
        repository.deleteAll(messages);
        return true;
    }

    public long countBySessionId(String sessionId) {
        return repository.findBySessionId(UUID.fromString(sessionId)).size();
    }

    // 편의 메서드들
    public List<ChatMessage> getUserMessages(String sessionId) {
        return repository.findByMessageType("user");
    }

    public List<ChatMessage> getAssistantMessages(String sessionId) {
        return repository.findByMessageType("assistant");
    }

    public List<ChatMessage> getSystemMessages(String sessionId) {
        return repository.findByMessageType("system");
    }
    
    // 슬라이딩 윈도우 관련 메서드들
    public List<ChatMessage> getRecentMessages(String sessionId, int limit) {
        return repository.findRecentBySessionId(UUID.fromString(sessionId), limit);
    }
    
    public List<ChatMessage> getRecentMessagesByTokenLimit(String sessionId, int maxTokens) {
        return repository.findRecentByTokenLimit(UUID.fromString(sessionId), maxTokens);
    }
    
    // turn_index 기반 슬라이딩 윈도우 (성능 최적화)
    public List<ChatMessage> getRecentMessagesByTurnIndex(String sessionId, int messageCount) {
        Integer maxTurnIndex = repository.findMaxTurnIndexBySessionId(UUID.fromString(sessionId));
        if (maxTurnIndex == null) {
            return new java.util.ArrayList<>();
        }
        
        Integer minTurnIndex = Math.max(1, maxTurnIndex - messageCount + 1);
        return repository.findBySessionIdAndTurnIndexGreaterThan(UUID.fromString(sessionId), minTurnIndex - 1);
    }
    
    // turn_index 기반 최근 N개 메시지 (가장 효율적)
    public List<ChatMessage> getLastNMessages(String sessionId, int n) {
        Integer maxTurnIndex = repository.findMaxTurnIndexBySessionId(UUID.fromString(sessionId));
        if (maxTurnIndex == null) {
            return new java.util.ArrayList<>();
        }
        
        Integer minTurnIndex = Math.max(1, maxTurnIndex - n + 1);
        return repository.findBySessionIdAndTurnIndexGreaterThan(UUID.fromString(sessionId), minTurnIndex - 1);
    }
    
    // department_id 관련 메서드들
    public List<ChatMessage> findByDepartmentId(Long departmentId) {
        return repository.findByDepartmentId(departmentId);
    }
    
    public List<ChatMessage> findByDepartmentIdAndSessionId(Long departmentId, String sessionId) {
        return repository.findByDepartmentIdAndSessionId(departmentId, UUID.fromString(sessionId));
    }
    
    public List<ChatMessage> findByDepartmentIdAndMessageType(Long departmentId, String messageType) {
        return repository.findByDepartmentIdAndMessageType(departmentId, messageType);
    }
    
    public List<ChatMessage> findActiveByDepartmentId(Long departmentId) {
        return repository.findActiveByDepartmentId(departmentId);
    }
}

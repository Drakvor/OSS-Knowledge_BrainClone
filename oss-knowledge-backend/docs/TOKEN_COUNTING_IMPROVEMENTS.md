# 토큰 계산 개선 계획

## 현재 상황

### 구현된 기능
- ✅ 사용자 메시지 토큰 계산 (`ChatController.java`)
- ✅ AI 응답 토큰 계산 (`ChatController.java`)
- ✅ 프론트엔드 컨텍스트 사용량 표시 (`ContextUsageIndicator.vue`)
- ✅ 실시간 토큰 사용량 업데이트

### 미구현 기능
- ❌ 검색된 문서 청크 토큰 계산
- ❌ Agent 도구 호출 결과 토큰 계산
- ❌ 전체 컨텍스트 토큰 정확한 계산

## 문제점

현재 RAG 시스템에서는 LLM에 전달되는 전체 컨텍스트가 다음과 같이 구성됩니다:

```
전체 컨텍스트 = 사용자 메시지 + 검색된 문서 청크들 + 시스템 프롬프트
```

하지만 현재는 **사용자 메시지 + AI 응답**만 계산하고 있어서, 실제 컨텍스트 사용량과 차이가 있습니다.

## 개선 방안

### 방안 1: 백엔드에서 통합 토큰 계산
- search-back에서 LLM 호출 전에 전체 컨텍스트를 백엔드로 전송
- 백엔드에서 토큰 계산 후 search-back에 결과 전달
- 장점: 모든 토큰 계산이 한 곳에서, Agent 추가 시에도 확장 가능

### 방안 2: 토큰 계산 서비스 분리
- 별도의 토큰 계산 마이크로서비스 생성
- 모든 서비스가 이 서비스를 호출해서 토큰 계산
- 장점: 독립적이고 확장 가능

### 방안 3: 하이브리드 방식
- 백엔드: 사용자 메시지 + AI 응답 토큰
- search-back: 검색된 문서 청크 토큰
- 각각 계산해서 합산

## Agent 추가 시 고려사항

Agent가 추가되면 다음과 같은 토큰 사용이 추가됩니다:
- 도구 호출 결과
- 도구 설명
- Agent 사고 과정
- 다중 턴 대화

이를 고려하여 확장 가능한 아키텍처를 설계해야 합니다.

## 구현 우선순위

1. **높음**: RAG 시스템 핵심 기능 완성
2. **중간**: Agent 아키텍처 설계
3. **낮음**: 정확한 토큰 계산 (현재 대략적 계산으로도 충분)

## 관련 파일들

### 백엔드
- `src/main/java/org/ossrag/meta/controller/ChatController.java` - 토큰 계산 로직
- `src/main/java/org/ossrag/meta/service/TokenCountService.java` - 토큰 계산 서비스
- `src/main/java/org/ossrag/meta/domain/ChatMessage.java` - 토큰 카운트 필드
- `src/main/java/org/ossrag/meta/domain/ChatSession.java` - 총 토큰 사용량 필드

### 프론트엔드
- `src/components/chat/ChatInput.vue` - 컨텍스트 사용량 표시
- `src/stores/conversation.js` - 토큰 데이터 관리

### 검색 서비스
- `app/api/routes/search.py` - LLM 호출 및 응답 생성
- `app/services/search_service.py` - 검색 서비스

## 참고사항

- 현재 `tiktoken` 라이브러리를 사용하여 토큰 계산
- GPT-4o 모델 기준 128K 토큰 컨텍스트 윈도우
- 실시간 토큰 사용량 업데이트를 위해 메시지 생성 시마다 `total_tokens_used` 필드 업데이트

## 마지막 업데이트

- 날짜: 2024년 12월
- 상태: 킵 (Agent 추가 시 전체 재설계 예정)
- 이유: 현재 대략적 계산으로도 충분하며, Agent 추가 시 아키텍처 변경 필요

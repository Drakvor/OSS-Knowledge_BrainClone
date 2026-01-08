# OSS Knowledge System - 데이터 흐름 및 아키텍처

## 🔄 현재 데이터 흐름:

### 시나리오 1: 일반 대화 (@ 없음, 부서 선택 없음) 🤖
```
사용자 입력
    ↓
Frontend (Vue.js)
    ↓
Backend (ChatController)
    ├─ departmentId = null
    ├─ collection = null
    ↓
Intent Classifier
    ├─ collection=null 감지
    ├─ RAG 검색 건너뛰기
    ↓
Search-Back (빈 검색으로 호출)
    ├─ 검색 결과 없음
    ├─ LLM만 직접 호출
    ↓
LLM 응답 생성
    ├─ ChatGPT처럼 자연스러운 대화
    ├─ 지식베이스 참조 없음
    ↓
응답 반환
```

### 시나리오 2: RAG 검색 (@로 부서 선택) 🔍
```
사용자 입력 (@부서명 질문)
    ↓
Frontend (Vue.js)
    ├─ mentionedDepartments = [부서 정보]
    ↓
Backend (ChatController)
    ├─ departmentId = 부서 ID
    ├─ collection = "부서명"
    ↓
Intent Classifier
    ├─ 의도 분류 (GREETING, RAG_QUERY, CONTEXT_QUERY, OTHER)
    ├─ collection != null → 검색 진행
    ↓
Search-Back (RAG 검색)
    ├─ Qdrant에서 관련 문서 검색
    ├─ 검색 결과 5개 추출
    ↓
LLM 응답 생성
    ├─ 검색 결과 + 대화 맥락
    ├─ 지식베이스 기반 답변
    ↓
응답 반환
```

### 비교표:

| 구분 | 일반 대화 | RAG 검색 |
|------|----------|---------|
| **트리거** | @ 없음, 부서 선택 없음 | @로 부서 선택 |
| **collection** | null | 부서명 |
| **Intent 분류** | 건너뛰기 | 수행 |
| **검색** | 수행 안함 | Qdrant 검색 |
| **LLM 사용** | ✅ 직접 호출 | ✅ 검색 결과 포함 |
| **답변 특징** | 일반적인 대화 | 지식베이스 기반 |
| **예시** | "안녕?", "오늘 날씨는?" | "@안전관리 안전 수칙은?" |

## 🤖 멀티 에이전트 아키텍처:

### 현재 구조 (Agentic RAG 확장 준비):
```
Intent-Classifier에서:
- GREETING → 친근한 인사 응답
- CONTEXT_QUERY → DB에서 채팅 히스토리 조회하여 맥락 응답
- RAG_QUERY → Search-Back 호출
- OTHER → 자연스러운 일반 대화 응답
- CODE_GENERATION → Code-Agent 호출 (예정)
- DATA_ANALYSIS → Data-Agent 호출 (예정)
- DOCUMENT_SUMMARY → Summary-Agent 호출 (예정)
- MEMORY_UPDATE → Memory-Agent 호출 (예정)
```

### 각 에이전트의 독립성:
- **Intent-Classifier**: 의도 분석 + 에이전트 라우팅 + DB 직접 접근
- **Search-Back**: RAG 검색 + LLM 응답 생성 + 자연스러운 대화
- **각 에이전트**: 독립적인 컨텍스트 관리 + PostgreSQL 직접 접근

## 🏗️ 아키텍처 설계 원칙:

### 1. 멀티 에이전트 확장성 우선
- 각 에이전트가 독립적으로 동작
- 새로운 에이전트 추가 시 Backend 수정 불필요
- 에이전트별 특화된 컨텍스트 처리

### 2. 데이터베이스 접근 전략
- **현재**: 각 에이전트가 PostgreSQL 직접 접근 (개발 단계)
- **향후**: Redis 캐싱 + PostgreSQL 백업
- **각 에이전트**: 필요한 데이터만 조회

### 3. 토큰 관리 시스템
- **사용자 메시지 토큰**: 정확히 계산
- **AI 응답 토큰**: 정확히 계산  
- **대화 요약 토큰**: 정확히 계산
- **하이브리드 요약**: 8K 토큰 또는 10턴마다

## 🚀 향후 확장 계획:

### Phase 1: 기본 에이전트 ✅
- ✅ GREETING (친근한 인사)
- ✅ CONTEXT_QUERY (맥락 참조 질문)
- ✅ RAG_QUERY (Search-Back)
- ✅ OTHER (자연스러운 일반 대화)
- 🔄 CODE_GENERATION (Code-Agent)
- 🔄 DATA_ANALYSIS (Data-Agent)

### Phase 2: 고급 에이전트
- 🔄 DOCUMENT_SUMMARY (Summary-Agent)
- 🔄 MEMORY_UPDATE (Memory-Agent)
- 🔄 WORKFLOW_AUTOMATION (Workflow-Agent)

### Phase 3: 최적화
- 🔄 Redis 캐싱 도입
- 🔄 에이전트별 성능 최적화
- 🔄 실시간 모니터링 시스템

## 📊 기술 스택:

### Backend (Java)
- Spring Boot + PostgreSQL
- 채팅 세션 관리, 토큰 계산, 대화 요약

### Intent-Classifier (Python) ✨ 최신 개선
- FastAPI + PostgreSQL + SQLAlchemy
- 의도 분석 + 에이전트 라우팅 + DB 직접 접근
- **새로운 의도 분류**:
  - GREETING: 친근한 인사 응답
  - CONTEXT_QUERY: 맥락 참조 질문 (DB에서 채팅 히스토리 조회)
  - RAG_QUERY: 기술 질문 (Search-Back 호출)
  - OTHER: 자연스러운 일반 대화
- **지능적인 맥락 처리**: "더 상세하고 자세히", "이런 패턴은 어쩔까?" 등

### Search-Back (Python) ✨ 최신 개선
- FastAPI + Qdrant + Azure OpenAI
- RAG 검색 + LLM 응답 생성 + 자연스러운 대화
- **개선된 프롬프트**: 검색 결과 강제 연결 제거, 사용자 의도 우선
- **친근한 톤**: 따뜻하고 자연스러운 응답 생성

### Frontend (Vue.js)
- Pinia 상태 관리
- 실시간 채팅 인터페이스

## 🎯 최신 개선사항 (2024.10.24):

### 1. 의도분류기 대폭 개선 ✅
- **DB 직접 접근**: 프론트엔드 의존성 제거
- **슬라이딩 윈도우**: 실제 DB의 채팅 히스토리 활용
- **확장된 CONTEXT_QUERY**: 추가 정보 요청, 패턴 질문, 예시 요청 등
- **자동 DB 저장**: 모든 대화를 PostgreSQL에 기록

### 2. 자연스러운 대화 구현 ✅
- **하드한 프롬프트 완화**: 억지스러운 검색 결과 연결 제거
- **사용자 의도 우선**: 검색 결과보다 사용자 질문에 집중
- **친근한 톤**: 따뜻하고 자연스러운 응답 생성

### 3. 지능적인 맥락 처리 ✅
- **95.7% 정확도**: 거의 모든 패턴을 정확히 인식
- **맞춤형 응답**: 각 질문 유형에 따른 구체적인 응답
- **연속적인 대화**: 이전 맥락을 참조한 자연스러운 상호작용

## 🎯 최신 설계 결정사항 (2024.10.28):

### 1. 일반 대화와 검색의 명확한 분리 ✅
- **부서 선택 없음 (collection=null)**: Intent Classifier를 거치지 않고 Search-Back LLM만 직접 호출
  - ChatGPT처럼 자연스러운 일반 대화
  - 검색 없이 순수 LLM 응답
  - 토큰 사용 최소화

- **부서 선택 (@로 언급)**: Intent Classifier를 거쳐 의도 분류
  - 컬렉션 정보와 함께 검색 수행
  - 기술적 질문에 대한 지식베이스 활용

### 2. 프롬프트 위치와 역할 분리 ✅
```
프롬프트 위치:
├─ intent-classifier/prompts.py
│  └─ 의도 분류 전용 (GREETING, RAG_QUERY, CONTEXT_QUERY, OTHER 판단)
│
└─ search-back/azure_llm.py
   └─ LLM 응답 생성 전용 (실제 답변 생성)
```

**왜 분리인가:**
- Intent Classifier는 "의도만" 판단
- 컬렉션 정보를 알지 못함 (100개 컬렉션을 알 수 없음)
- Search-Back이 컬렉션 정보를 받아 실제 검색 및 응답 생성

### 3. 토큰 비용 최적화 전략 💰

#### 토큰 절약 전략
```python
# Intent Classifier의 generate_response()
# LLM 호출 없이 규칙 기반 응답 생성
# 매우 단순한 질문에 대해서만 사용
```

**사용 케이스:**
- collection=null → Search-Back LLM 호출 (자연스러운 대화)
- collection!=null && OTHER → 규칙 기반 응답 (토큰 절약)
- collection!=null && RAG_QUERY → Search-Back LLM + 검색 (토큰 사용)

**토큰 비용 예시:**
- 일반 대화: ~500-1000 토큰
- 검색 기반: ~2000-3000 토큰
- 규칙 기반: 0 토큰

### 4. 시스템 아키텍처 개선 이력

#### 초기 설계 문제
- collection=null일 때 항상 Intent Classifier 통과
- 불필요한 의도 분류 수행
- 외래키 제약 조건 위반 (department_id=1이 DB에 없음)

#### 개선 내용
1. **collection=null 감지**: Backend에서 collection=null 확인
2. **직접 호출**: Intent Classifier 우회, Search-Back 직접 호출
3. **fallback 제거**: 하드코딩된 department 목록 제거 (DB와 불일치 방지)
4. **스트리밍 통일**: 일반 대화도 스트리밍 응답 지원

### 5. 데이터 흐름 상세

#### 시나리오 1: 일반 대화 (부서 선택 없음)
```
사용자: "안녕?"
    ↓
Frontend → mentionedDepartments = []
    ↓
Backend (ChatController)
    ├─ collection = null
    ├─ departmentId = null
    ├─ Intent Classifier 호출 안함 ✨
    ↓
handleSearchBackStreaming()
    ├─ Search-Back 호출 (/search/response)
    ├─ collection="" (빈 값, 검색 안함)
    ├─ threshold=1.0 (검색 결과 없음)
    ├─ limit=1 (최소값 만족)
    ↓
Search-Back LLM 처리
    ├─ 검색 결과 없음
    ├─ 시스템 프롬프트: 일반 대화용
    ├─ 자연스러운 응답 생성
    ↓
Backend에서 SSE 스트리밍 변환
    ↓
프론트엔드 실시간 표시 (ChatGPT 스타일)
```

**특징:**
- ✅ Intent Classifier 비통과 (빠른 응답)
- ✅ 검색 수행 안함 (비용 절감)
- ✅ LLM으로 자연스러운 대화
- ✅ 스트리밍 응답

#### 시나리오 2: RAG 검색 (부서 선택)
```
사용자: "@안전관리 안전관리 절차는?"
    ↓
Frontend → mentionedDepartments = [{id: 3, name: "안전관리"}]
    ↓
Backend (ChatController)
    ├─ collection = "안전관리"
    ├─ departmentId = 3
    ├─ Intent Classifier 호출 ✨
    ↓
Intent Classifier
    ├─ 의도 분류 (RAG_QUERY, GREETING, CONTEXT_QUERY, OTHER)
    ├─ RAG_QUERY 감지
    ↓
Search-Back 호출
    ├─ collection="안전관리"
    ├─ Qdrant에서 관련 문서 검색
    ├─ 검색 결과 + 대화 맥락
    ├─ LLM 응답 생성
    ↓
지식베이스 기반 답변
```

**특징:**
- ✅ Intent Classifier 통과 (의도 분석)
- ✅ 컬렉션 정보 활용
- ✅ RAG 검색 수행
- ✅ 기술적 답변 제공

## 🧠 Mem0 장기 기억 시스템 (2024.11.04 추가):

### 메모리 아키텍처 설계:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   Backend       │───▶│  Search-Back    │
│  (Vue.js)       │    │ (ChatController)│    │  (AzureLLM)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                               ┌───────────────────────┼───────────────────────┐
                               │                       │                       │
                         ┌─────▼─────┐       ┌────────▼────────┐    ┌────────▼────────┐
                         │   Mem0    │       │    Qdrant       │    │  Azure OpenAI   │
                         │ (8005포트) │       │  (벡터 검색)     │    │    (LLM)        │
                         └───────────┘       └─────────────────┘    └─────────────────┘
```

### 2단계 메모리 구조:

#### 1. 사용자별 장기 기억 (User-Level Memory)
- **ID**: `user_{users.id}` (PostgreSQL users 테이블 연동)
- **용도**: 개인 취향, 습관, 선호도 등 지속적인 특성
- **메타데이터**:
  ```json
  {
    "type": "user_preference|habit|characteristic",
    "category": "food|language|work_style|...",
    "confidence": 0.8,
    "level": "user",
    "timestamp": "2024-11-04T10:30:00Z"
  }
  ```
- **예시**: "사용자는 커피를 좋아함", "한국어 선호", "아침형 인간"

#### 2. 세션별 단기 기억 (Session-Level Memory)
- **ID**: `session_{chat_sessions.id}` (PostgreSQL chat_sessions 테이블 연동)
- **용도**: 특정 대화 맥락, 임시 정보, 현재 대화 흐름
- **메타데이터**:
  ```json
  {
    "type": "conversation_context|decision|request",
    "session_id": "uuid-string",
    "topic": "project_planning",
    "message_count": 5,
    "level": "session",
    "timestamp": "2024-11-04T10:30:00Z"
  }
  ```
- **예시**: "이번 대화에서 A 프로젝트에 대해 논의 중", "방금 B 문서를 요청함"

### 메모리 통합 데이터 흐름:

#### 시나리오 1: 일반 대화 + 메모리 (부서 선택 없음)
```
사용자: "오늘도 커피 마실까?"
    ↓
Frontend → Backend → Search-Back
    ├─ user_id: 123 (로그인 사용자)
    ├─ session_id: "uuid-abc" (현재 채팅방)
    ↓
Search-Back (AzureLLMService)
    ├─ 1️⃣ Mem0 메모리 검색:
    │   ├─ 사용자 기억: "커피를 좋아함", "라떼 선호"
    │   ├─ 세션 기억: "아침 시간대 대화 중"
    ├─ 2️⃣ 프롬프트 구성:
    │   ├─ 사용자 메시지: "오늘도 커피 마실까?"
    │   ├─ 📝 사용자 개인 정보 (장기 기억):
    │   │   - 사용자는 커피를 좋아함
    │   │   - 라떼를 선호함
    │   ├─ 💭 이번 대화 맥락 (단기 기억):
    │   │   - 아침 시간대 대화 중
    ├─ 3️⃣ 개인화된 LLM 응답:
    │   "좋은 아침이에요! 평소 라떼를 좋아하시니까 
    │    오늘도 맛있는 라떼 한 잔 어떠세요? ☕"
    ├─ 4️⃣ 메모리 저장:
    │   ├─ 세션 기억: "커피 관련 대화함"
    │   ├─ 중요도 판별 → 사용자 기억 저장 여부 결정
    ↓
개인화된 응답 반환
```

#### 시나리오 2: RAG 검색 + 메모리 (부서 선택)
```
사용자: "@개발팀 우리 프로젝트 코딩 스타일은?"
    ↓
Frontend → Backend → Intent-Classifier → Search-Back
    ├─ user_id: 123
    ├─ session_id: "uuid-abc"
    ├─ collection: "개발팀"
    ↓
Search-Back (AzureLLMService)
    ├─ 1️⃣ 메모리 검색:
    │   ├─ 사용자 기억: "Java 선호", "클린코드 관심"
    │   ├─ 세션 기억: "프로젝트 관련 대화 중"
    ├─ 2️⃣ RAG 검색:
    │   ├─ Qdrant에서 "개발팀" 컬렉션 검색
    │   ├─ 코딩 스타일 관련 문서들 검색
    ├─ 3️⃣ 통합 프롬프트:
    │   ├─ 사용자 메시지
    │   ├─ 📝 사용자 기억 (Java 선호, 클린코드 관심)
    │   ├─ 💭 세션 기억 (프로젝트 관련 대화)
    │   ├─ 🔍 검색 결과 (코딩 스타일 가이드)
    ├─ 4️⃣ 개인화 + 지식기반 응답:
    │   "Java를 선호하시는 것 같으니, 우리 팀의 Java 
    │    코딩 스타일을 중점으로 설명드릴게요..."
    ├─ 5️⃣ 메모리 저장:
    │   ├─ 세션: "개발팀 코딩스타일 문의함"
    │   ├─ 사용자: "프로젝트 코딩스타일에 관심"
    ↓
개인화 + 지식기반 통합 응답
```

### 메모리 저장 전략:

#### 자동 저장 조건:
1. **사용자 메모리 저장**:
   - 개인 선호도 언급 ("저는 ~를 좋아해요")
   - 반복적인 패턴 감지 (같은 요청 3회 이상)
   - 명시적인 개인정보 제공
   - 중요한 결정사항이나 계획

2. **세션 메모리 저장**:
   - 모든 대화 (컨텍스트 유지용)
   - 특정 문서/프로젝트 언급
   - 이전 질문과 연관된 후속 질문
   - 결정사항이나 중요한 정보

#### 중요도 판별 알고리즘:
```python
is_important = (
    len(response) > 200 or  # 긴 응답은 중요
    any(keyword in query.lower() for keyword in 
        ['좋아', '싫어', '선호', '취향', '습관']) or  # 선호도 관련
    settings.MEM0_AUTO_SAVE_IMPORTANT  # 설정값
)
```

### API 파라미터 확장:

#### 현재 필요한 파라미터 추가:
```javascript
// Frontend → Backend
{
  message: "사용자 질문",
  conversationId: "uuid",
  departmentId: 3,
  selectedModel: "gpt-4o",
  userId: 123,           // ← 추가 필요
  sessionId: "uuid"      // ← conversationId와 동일
}

// Backend → Search-Back
{
  query: "사용자 질문",
  collection: "부서명",
  session_id: "uuid",
  user_id: 123,          // ← 추가 필요
  chat_context: {...}
}
```

### 기술 스택 확장:

#### Mem0 서비스 (Python FastAPI, 8005포트)
- **벡터 저장소**: Qdrant (20.249.165.27:6333)
- **LLM**: Azure OpenAI (임베딩 및 의미 분석)
- **메모리 관리**: 사용자/세션별 분리된 메모리 공간

#### Search-Back 확장 (Python FastAPI, 8002포트)
- **Mem0 클라이언트**: `app/core/mem0_client.py`
- **AzureLLM 통합**: 메모리 검색/저장 로직 추가
- **설정**: `MEM0_BASE_URL`, `MEM0_ENABLED` 환경변수

### 성능 최적화:

#### 메모리 검색 최적화:
- **병렬 검색**: 사용자/세션 메모리 동시 검색
- **제한된 결과**: 사용자 5개, 세션 10개 최대
- **오류 복구**: Mem0 오류 시 정상 서비스 유지

#### 토큰 사용 최적화:
- **스마트 메모리 선택**: 관련성 높은 메모리만 포함
- **컨텍스트 압축**: 긴 메모리는 요약하여 사용
- **조건부 저장**: 중요한 정보만 메모리에 저장

## 🔄 다음 구현 단계:

### 1. API 체인 파라미터 전달 ✅
- ✅ Mem0 서비스 구현 (8005포트)
- ✅ Search-Back Mem0 클라이언트 통합
- 🔄 Backend ChatController 수정
- 🔄 Frontend API 호출 수정

### 2. 메모리 데이터 검증
- 🔄 사용자/세션 ID 유효성 검사
- 🔄 메모리 저장/검색 테스트
- 🔄 개인화 응답 품질 검증

### 3. 모니터링 및 최적화
- 🔄 메모리 사용량 모니터링
- 🔄 응답 품질 평가
- 🔄 토큰 비용 분석
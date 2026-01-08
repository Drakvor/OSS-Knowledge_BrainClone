# 의도분류기 아키텍처 평가 - 멀티 에이전트 허브 설계

## 현재 구조

```
Frontend
    ↓
Backend (흐름 제어 + DB 저장)
    ↓
Intent Classifier (중앙 허브)
    ├─ intent 분류
    ├─ 에이전트 라우팅
    ├─ Search-Back 호출 (RAG)
    ├─ Code-Agent 호출 (예정)
    ├─ Data-Agent 호출 (예정)
    └─ Memory-Agent 호출 (예정)
    ↓
응답 반환
```

## 설계 평가

### ✅ 장점

#### 1. **명확한 책임 분리**
- Backend: 흐름 제어만
- Intent Classifier: 의도 파악 + 에이전트 선택
- 각 에이전트: 특정 작업 수행
- Backend 코드는 에이전트 추가 시 수정 불필요

#### 2. **확장성 우수**
```python
# 새 에이전트 추가 시 main.py만 수정
if intent == "CODE_GENERATION":
    response = await code_agent.generate(code_request)
elif intent == "DATA_ANALYSIS":
    response = await data_agent.analyze(data_request)
# Backend 변경 불필요!
```

#### 3. **통합된 컨텍스트 관리**
- Intent Classifier가 session_id 관리
- 모든 에이전트가 동일한 대화 맥락 공유
- 슬라이딩 윈도우 자동 처리

#### 4. **에러 격리**
- 한 에이전트 장애 시 fallback 가능
- 다른 에이전트는 정상 동작

### ⚠️ 우려사항

#### 1. **Intent Classifier 부담 (God Object)**
**현재:** Intent Classifier가 너무 많은 책임
```python
Intent Classifier (현재)
├─ 의도 분류
├─ Search-Back 호출
├─ 에러 처리
├─ 기본 응답 생성
└─ 향후 모든 에이전트 관리
```

**해결책:** 팩토리 패턴 도입
```python
class AgentRouter:
    def route(self, intent: str, message: str, session_id: str):
        agent = self.agent_factory.create(intent)
        return agent.process(message, session_id)
```

#### 2. **순환 의존성 위험**
```python
# 만약 에이전트끼리 호출해야 한다면?
Code-Agent → Search-Back 호출?
Data-Agent → Summary-Agent 호출?

# 이 경우 Intent Classifier가 또 라우팅?
# 복잡해질 수 있음
```

**해결책:** 메시지 버스 도입
```python
# 에이전트끼리는 직접 호출하지 않고 이벤트로 통신
code_agent.publish("need_data_analysis", data)
# 메시지 버스가 routing
```

#### 3. **단일 장애점 (SPOF)**
Intent Classifier가 죽으면 전체 시스템 마비

**해결책:** Circuit Breaker 패턴
```python
@circuit_breaker(failure_threshold=5)
async def call_agent():
    ...
    # 5번 실패하면 자동으로 차단
```

## 개선 제안

### 단기 (지금 적용 가능)

#### 1. **Agent Router 패턴**
```python
class AgentRouter:
    def __init__(self):
        self.agents = {
            "RAG_QUERY": SearchAgent(),
            "CODE_GENERATION": CodeAgent(),  # 향후
            "DATA_ANALYSIS": DataAgent(),    # 향후
        }
    
    async def route(self, intent: str, request: ChatRequest) -> str:
        agent = self.agents.get(intent)
        if not agent:
            agent = self.agents["RAG_QUERY"]  # default
        return await agent.process(request)
```

#### 2. **에러 처리 강화**
```python
try:
    response = await self.agents[intent].process(request)
except AgentNotAvailableError:
    # 다음 우선순위 에이전트로 fallback
    response = await self.fallback_agent.process(request)
except Exception as e:
    logger.error(f"Agent {intent} failed: {e}")
    response = "죄송합니다. 일시적인 오류가 발생했습니다."
```

### 장기 (향후 확장)

#### 1. **이벤트 기반 아키텍처**
```
Intent Classifier (Publisher)
    ↓ event: {intent, message, session_id}
Message Bus
    ↓
각 에이전트 (Subscriber)
    ↓
결과 반환
```

#### 2. **에이전트 체이닝**
```
사용자: "이 코드 리뷰하고 배포까지 해줘"
    ↓
Intent Classifier → Multi-Agent Workflow
    ├─ Code-Agent (리뷰)
    ├─ Deployment-Agent (배포)
    └─ Notification-Agent (알림)
```

#### 3. **마이크로서비스 분리**
```
Intent Classifier (API Gateway)
    ├─ /agents/search
    ├─ /agents/code
    ├─ /agents/data
    └─ /agents/memory
```

## 최종 평가

| 항목 | 점수 | 평가 |
|------|------|------|
| 확장성 | 9/10 | 새 에이전트 추가 쉬움 |
| 유지보수성 | 7/10 | Intent Classifier 집중도 높음 |
| 안정성 | 6/10 | SPOF 위험 (해결 필요) |
| 성능 | 8/10 | 비동기 처리 우수 |
| 테스트 용이성 | 7/10 | 모킹 필요 |

### 종합: 7.4/10

**결론:** 현 구조는 확장성에 강점이 있다. 단, 에이전트가 늘어나면 라우팅과 에러 처리를 더 체계화하는 방향으로 정리가 필요하다.


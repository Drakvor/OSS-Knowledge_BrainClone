# OSS Knowledge Backend API

OSS 지식 관리 시스템의 백엔드 API 서버입니다. RAG(Retrieval-Augmented Generation) 기반의 지식 검색 및 대화 관리 기능을 제공합니다.

## 기술 스택
- **Java**: JDK 21
- **Framework**: Spring Boot 3.2.4
- **Build Tool**: Maven 3.9.10
- **Database**: PostgreSQL with JPA/Hibernate
- **ORM**: Spring Data JPA + Hibernate Types (JSONB 지원)
- **API Documentation**: springdoc-openapi 2.5.0 (Swagger)
- **Logging**: JSON structured logging with requestId/sessionId
- **Testing**: Testcontainers 1.19.7
- **Security**: JWT Authentication
- **Code Generation**: Lombok

## 주요 기능
- **에이전트 관리**: RAG 에이전트 등록, 조회, 수정, 삭제
- **대화 관리**: 사용자와 AI 간의 대화 기록 관리 (세션, 메시지, 피드백)
- **인증/인가**: JWT 기반 사용자 인증
- **RAG 부서 관리**: 조직별 RAG 시스템 관리
- **JSONB 지원**: PostgreSQL JSONB 필드 자동 처리

## 설치 및 실행 방법

### 1. 환경 요구사항
- JDK 21
- Maven 3.9.10
- PostgreSQL 16+
- Podman/Docker (테스트용)

### 2. 데이터베이스 설정
   ```bash
# PostgreSQL 컨테이너 실행 (선택사항)
podman run --name oss-knowledge-postgres \
  -e POSTGRES_DB=oss_knowledge \
  -e POSTGRES_USER=oss -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 -d postgres:16
   ```

### 3. 데이터베이스 스키마 적용
   ```bash
# PostgreSQL에 직접 스키마 적용
   podman exec -i oss-knowledge-postgres psql -U oss -d oss_knowledge < sql/01_database_schema.sql
   ```

### 4. 환경 변수 설정
```bash
export DB_URL=jdbc:postgresql://localhost:5432/oss_knowledge
export DB_USERNAME=oss
export DB_PASSWORD=changeme
export JWT_SECRET=your-jwt-secret-key
export EMBEDDING_BACKEND_URL=http://localhost:8000
export SEARCH_SERVER_URL=http://localhost:8002
```

### 5. 애플리케이션 실행
   ```bash
# 빌드
   mvn clean package

# 실행
   mvn spring-boot:run

# 또는 JAR 파일로 실행
java -jar target/ossrag-meta-api-0.0.1-SNAPSHOT.jar
```

## 프로젝트 구조

```
src/main/java/org/ossrag/meta/
├── config/           # 설정 클래스들
│   ├── SecurityConfig.java      # 보안 설정
│   ├── CorsConfig.java         # CORS 설정
│   ├── JwtAuthFilter.java      # JWT 인증 필터
│   └── SwaggerConfig.java      # Swagger 설정
├── controller/       # REST API 컨트롤러
│   ├── AgentController.java           # 에이전트 관리
│   ├── AuthController.java            # 인증
│   ├── ChatController.java            # 채팅
│   ├── RAGDepartmentController.java   # RAG 부서 관리
│   └── AzureController.java           # Azure AI 연동
├── domain/          # JPA 엔티티 (도메인 모델)
│   ├── Agent.java              # 에이전트 엔티티
│   ├── ChatSession.java        # 채팅 세션 엔티티
│   ├── ChatMessage.java        # 채팅 메시지 엔티티
│   ├── ChatMessageFeedback.java # 메시지 피드백 엔티티
│   ├── RAGDepartment.java      # RAG 부서 엔티티
│   └── User.java               # 사용자 엔티티
├── repository/      # JPA Repository 인터페이스
│   ├── AgentRepository.java
│   ├── ChatSessionRepository.java
│   ├── ChatMessageRepository.java
│   ├── ChatMessageFeedbackRepository.java
│   ├── RAGDepartmentRepository.java
│   └── UserRepository.java
├── dto/             # 데이터 전송 객체
├── service/         # 비즈니스 로직
└── error/           # 예외 처리
```

## API 엔드포인트

### 인증 API
- `POST /auth/login` - 사용자 로그인
- `POST /auth/token` - JWT 토큰 발급

### 에이전트 관리 API
- `GET /agents` - 에이전트 목록 조회
- `POST /agents` - 에이전트 생성
- `GET /agents/{agentId}` - 에이전트 상세 조회
- `PUT /agents/{agentId}` - 에이전트 수정
- `DELETE /agents/{agentId}` - 에이전트 삭제

### RAG 부서 관리 API
- `GET /rag-departments` - RAG 부서 목록 조회
- `POST /rag-departments` - RAG 부서 생성
- `GET /rag-departments/{id}` - RAG 부서 상세 조회
- `PUT /rag-departments/{id}` - RAG 부서 수정
- `DELETE /rag-departments/{id}` - RAG 부서 삭제
- `PATCH /rag-departments/{id}/status` - 부서 상태 변경
- `GET /rag-departments/stats` - 부서 통계 조회

### 채팅 API
- `POST /chat` - 채팅 메시지 전송
- `POST /chat/search-engine` - 검색 엔진 채팅

### 채팅 세션 관리 API
- `GET /chat/sessions` - 세션 목록 조회
- `GET /chat/sessions/recent` - 최근 세션 조회
- `GET /chat/sessions/{id}` - 세션 상세 조회
- `POST /chat/sessions` - 세션 생성
- `PUT /chat/sessions/{id}` - 세션 수정
- `DELETE /chat/sessions/{id}` - 세션 삭제

### 채팅 메시지 관리 API
- `GET /chat/sessions/{sessionId}/messages` - 메시지 목록 조회
- `GET /chat/sessions/{sessionId}/messages/ordered` - 정렬된 메시지 조회
- `POST /chat/sessions/{sessionId}/messages` - 메시지 생성

### 메시지 피드백 API
- `POST /chat/messages/{messageId}/feedback` - 피드백 생성
- `GET /chat/messages/{messageId}/feedback` - 피드백 조회
- `GET /chat/messages/{messageId}/feedback/stats` - 피드백 통계

### Azure AI 연동 API
- `GET /azure/connection-status` - Azure 연결 상태 확인
- `POST /azure/sync` - Azure 동기화

### 헬스체크 API
- `GET /healthz` - 헬스체크
- `GET /health` - 헬스체크 (상세)

## 데이터베이스 스키마

### 주요 테이블
- `agents`: 에이전트 정보 (VARCHAR)
- `chat_sessions`: 채팅 세션 정보 (UUID)
- `chat_messages`: 채팅 메시지 정보 (UUID)
- `chat_message_feedback`: 메시지 피드백 정보 (UUID)
- `rag_departments`: RAG 부서 정보 (BIGSERIAL)
- `users`: 사용자 정보 (BIGSERIAL)

### 식별자 규칙
- **채팅 관련 엔티티**: UUID 형식 사용 (`@GeneratedValue(strategy = GenerationType.UUID)`)
- **사용자/부서**: BIGSERIAL (자동 증가 정수)
- **에이전트**: VARCHAR(26) (사용자 정의 ID)
- **Request ID**: UUID 형식 사용 (`UUID.randomUUID().toString()`)
- 타임스탬프는 UTC ISO-8601 형식
- 소프트 삭제는 `deleted_at` 컬럼으로 구현

## 환경 설정

### 필수 환경 변수
```bash
# 데이터베이스 연결
DB_URL=jdbc:postgresql://localhost:5432/oss_knowledge
DB_USERNAME=oss
DB_PASSWORD=changeme

# 보안 설정
JWT_SECRET=your-jwt-secret-key-here
API_KEY=your-api-key-here

# 외부 서비스 연동 (실제 포트 번호 반영)
EMBEDDING_BACKEND_URL=http://localhost:8000
SEARCH_SERVER_URL=http://localhost:8002
```

### 선택적 환경 변수
```bash
# IP 화이트리스트 (기본값: 모든 IP 허용)
SECURITY_IP_ALLOWLIST=*

# JWT 토큰 만료 시간 (분)
SECURITY_JWT_ACCESS_EXP_MIN=480

# JWT 리프레시 토큰 만료 시간 (일)
SECURITY_JWT_REFRESH_EXP_DAYS=7
```

## API 문서 및 테스트

### Swagger UI
- URL: `http://localhost:8080/swagger-ui.html`
- OpenAPI 명세: `http://localhost:8080/api-docs`
- Swagger 설정: `src/main/java/org/ossrag/meta/config/SwaggerConfig.java`
- API 스펙 파일: `swagger/swagger.yaml`

### 인증 방법
1. **JWT 토큰**: `Authorization: Bearer <token>` 헤더 사용
2. **요청 추적**: `X-Request-Id: <uuid>` 헤더 사용 (선택사항)

### 토큰 발급 예시
```bash
# 로그인
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 토큰 발급 (개발용)
curl -X POST http://localhost:8080/auth/token \
  -H "Content-Type: application/json" \
  -d '{"userId": "test-user"}'
```

### API 응답 구조
```json
// 로그인 응답
{
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresAt": "2024-01-01T12:00:00Z",
    "refreshExpiresAt": "2024-01-08T12:00:00Z"
  },
  "message": "Login successful"
}
```

## 테스트

### 단위 테스트 실행
```bash
mvn test
```

### 통합 테스트 실행
```bash
mvn verify
```

### 테스트 컨테이너 건너뛰기
```bash
mvn test -DskipTests
mvn verify -DskipITs
```

## 배포

### Docker 이미지 빌드
```bash
# Jenkins 파이프라인 사용
# devops/Jenkinsfile 참조

# 수동 빌드
mvn clean package
docker build -f docker/api/Dockerfile -t oss-knowledge-api .
```

### Kubernetes 배포
```bash
# ArgoCD를 통한 GitOps 배포
# devops/argocd-app.yaml 참조

# 수동 배포
kubectl apply -f k8s/
```

## 로깅

### 로그 형식
- JSON 한 줄 형식
- 필수 필드: `timestamp`, `level`, `logger`, `message`
- 컨텍스트 필드: `requestId`, `sessionId`

### 로그 레벨 설정
```yaml
logging:
  level:
    org.ossrag.meta: DEBUG
    root: INFO
```

## 모니터링

### Health Check
- URL: `http://localhost:8080/actuator/health`
- Prometheus 메트릭: `http://localhost:8080/actuator/prometheus`

## 트러블슈팅

### 일반적인 문제
1. **데이터베이스 연결 실패**: 환경 변수 확인
2. **JWT 토큰 만료**: 토큰 갱신 또는 재발급
3. **CORS 오류**: 프론트엔드 도메인 설정 확인
4. **API Key 오류**: 헤더 형식 및 값 확인

### 로그 확인
```bash
# 애플리케이션 로그 확인
tail -f logs/application.log

# 데이터베이스 로그 확인
podman logs oss-knowledge-postgres
```

## 프론트엔드 연동

### 실제 연동 구조
프론트엔드는 3개의 백엔드 서비스와 연동합니다:

1. **Java Backend (Meta API)**: `src/services/metaApi.js`
   - 인증, 부서 관리, 대화 관리, 문서 관리
   - 기본 URL: `VITE_API_BASE_URL` (기본값: `http://localhost:8080`)

2. **Python Search Backend**: `src/services/searchApi.js`
   - 검색, RAG, 채팅, Graph RAG
   - 기본 URL: `VITE_SEARCH_API_BASE_URL` (기본값: `http://localhost:8002`)

3. **Python Embedding Backend**: `src/services/embeddingApi.js`
   - 문서 처리, 임베딩, 청킹, 벡터 저장
   - 기본 URL: `VITE_EMBEDDING_API_BASE_URL` (기본값: `http://localhost:8000`)

### 환경 변수 설정
```env
# .env
VITE_API_BASE_URL=http://localhost:8080
VITE_SEARCH_API_BASE_URL=http://localhost:8002
VITE_EMBEDDING_API_BASE_URL=http://localhost:8000
```

### 주요 API 사용 예시
```javascript
// 인증
import { loginAPI, getAuthTokenAPI } from '@/services/metaApi';

// 로그인
const authData = await loginAPI('username', 'password');

// 토큰 발급 (개발용)
const tokenData = await getAuthTokenAPI('test-user');

// 검색/채팅
import { sendMessageAPI } from '@/services/searchApi';
const response = await sendMessageAPI({
  message: '질문 내용',
  conversationId: 'conversation-id',
  selectedDepartments: ['dept1', 'dept2']
  });
  ```

## 개발 가이드

### 코드 스타일
- Java 21 문법 사용
- UUID 식별자 사용 (JPA @GeneratedValue)
- UTC 타임스탬프 사용 (@CreationTimestamp, @UpdateTimestamp)
- JSON 구조화 로깅
- Lombok 어노테이션 활용 (@Getter, @Setter, @NoArgsConstructor)

### JPA 개발
- Spring Data JPA Repository 패턴 사용
- PostgreSQL JSONB 필드 자동 처리 (@Type(JsonType.class))
- 메서드명 쿼리 활용 (findBy, countBy 등)
- 복잡한 쿼리는 @Query 어노테이션 사용

### API 개발
- OpenAPI 3.1 명세 준수
- Swagger 어노테이션 사용
- 입력 검증 필수
- 에러 응답 표준화
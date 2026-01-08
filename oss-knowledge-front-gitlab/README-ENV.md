# 환경 설정 가이드

## 환경 변수 파일

프로젝트는 환경별로 다른 설정을 사용할 수 있도록 다음과 같은 환경 변수 파일을 지원합니다:

### 파일 구조

```
.env.example          # 환경 변수 예시 파일
.env.development      # 개발 환경 기본값
.env.local           # 로컬 개발 환경 (우선순위 높음)
.env.production      # 프로덕션 환경
```

### 환경 변수 우선순위

1. `.env.local` (최고 우선순위)
2. `.env.development` 또는 `.env.production` (모드에 따라)
3. `vite.config.js`의 기본값

### 사용 가능한 환경 변수

| 변수명                        | 설명                                 | 기본값                  | 백엔드 서비스    |
| ----------------------------- | ------------------------------------ | ----------------------- | ---------------- |
| `VITE_API_BASE_URL`           | Meta API 백엔드 URL (Java)           | `http://localhost:8080` | Meta API         |
| `VITE_EMBEDDING_API_BASE_URL` | Embedding API 백엔드 URL (Python)    | `http://localhost:8000` | Embedding API    |
| `VITE_SEARCH_API_BASE_URL`    | Search API 백엔드 URL (Python)       | `http://localhost:8002` | Search API       |
| `VITE_ORCHESTRATOR_URL`       | Orchestrator API 백엔드 URL (Python) | `http://localhost:8000` | Orchestrator API |

### 백엔드 서비스별 포트 정보

| 서비스               | 포트 | 기술 스택        | 실행 명령어                                                |
| -------------------- | ---- | ---------------- | ---------------------------------------------------------- |
| **Meta API**         | 8080 | Java Spring Boot | `mvn spring-boot:run`                                      |
| **Embedding API**    | 8000 | Python FastAPI   | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| **Orchestrator API** | 8000 | Python FastAPI   | `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`     |
| **Search API**       | 8002 | Python FastAPI   | `uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload` |

### 실행 명령어

#### 개발 환경

```bash
# 개발 모드 (기본)
npm run dev

# 로컬 모드 (로컬 설정 우선)
npm run dev:local
```

#### 빌드

```bash
# 프로덕션 빌드
npm run build

# 로컬 빌드
npm run build:local
```

### 환경별 설정 예시

#### 로컬 개발 (.env.local)

```env
# Meta API (Java Backend) - 부서 관리, 인증, 권한
VITE_API_BASE_URL=http://localhost:8080

# Embedding API (Python Backend) - 문서 처리, 임베딩, 청킹
VITE_EMBEDDING_API_BASE_URL=http://localhost:8000

# Search API (Python Backend) - 검색, RAG, Graph RAG, 채팅
VITE_SEARCH_API_BASE_URL=http://localhost:8002

# Orchestrator API (Python Backend) - 오케스트레이션, 의도 분류, 작업 계획
VITE_ORCHESTRATOR_URL=http://localhost:8000
```

#### 프로덕션 (.env.production)

```env
# Meta API (Java Backend)
VITE_API_BASE_URL=https://api.oss-knowledge.com

# Embedding API (Python Backend)
VITE_EMBEDDING_API_BASE_URL=https://embedding.oss-knowledge.com

# Search API (Python Backend)
VITE_SEARCH_API_BASE_URL=https://search.oss-knowledge.com

# Orchestrator API (Python Backend)
VITE_ORCHESTRATOR_URL=https://orchestrator.oss-knowledge.com
```

### 백엔드 서비스 실행 순서

프론트엔드가 정상적으로 작동하려면 다음 순서로 백엔드 서비스들을 실행하세요:

1. **Meta API (포트 8080)** - 먼저 실행

    ```bash
    cd oss-knowledge-backend
    mvn spring-boot:run
    ```

2. **Embedding API (포트 8000)** - 문서 처리용

    ```bash
    cd oss-knowledge-embedding-back
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

3. **Search API (포트 8002)** - 검색 및 채팅용

    ```bash
    cd oss-knowledge-search-back
    uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
    ```

4. **프론트엔드 (포트 5173)** - 마지막에 실행
    ```bash
    cd oss-knowledge-front
    npm run dev
    ```

### 설정 방법

1. **로컬 개발**: `.env.local` 파일을 생성하고 로컬 서버 주소를 설정
2. **프로덕션**: `.env.production` 파일에 실제 서버 주소를 설정
3. **팀 공유**: `.env.example` 파일을 참고하여 각자 환경에 맞게 설정

### 주의사항

-   `.env.local` 파일은 Git에 커밋하지 마세요 (이미 .gitignore에 포함됨)
-   `.env.production` 파일은 실제 서버 주소를 사용하세요
-   환경 변수는 `VITE_` 접두사가 있어야 프론트엔드에서 사용할 수 있습니다
-   백엔드 서비스들이 모두 실행된 후 프론트엔드를 실행하세요
-   포트 충돌이 발생하면 각 서비스의 포트를 확인하세요

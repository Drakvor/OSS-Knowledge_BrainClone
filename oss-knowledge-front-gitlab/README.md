# OSS Knowledge Front (Brain Clone)

Vue.js 기반의 OSS 지식 관리 프론트엔드 애플리케이션입니다.

## 프로젝트 개요

이 프로젝트는 OSS 지식 관리를 위한 멀티 에이전트 플랫폼의 프론트엔드입니다. 다음과 같은 백엔드 서비스들과 연동됩니다:

- **Meta API** (Java Backend) - 부서 관리, 사용자 인증, 권한 관리
- **Embedding API** (Python Backend) - 문서 처리, 임베딩, 청킹
- **Search API** (Python Backend) - 검색, RAG, Graph RAG, 채팅

## 기술 스택

- **Frontend**: Vue.js 3, Pinia, Vue Router
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Markdown**: Marked.js

## 설치 및 실행

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env.local` 파일을 생성하고 필요한 환경 변수를 설정하세요:

```env
# Meta API (Java Backend)
VITE_API_BASE_URL=http://localhost:8080

# Embedding API (Python Backend)  
VITE_EMBEDDING_API_BASE_URL=http://localhost:8000

# Search API (Python Backend)
VITE_SEARCH_API_BASE_URL=http://localhost:8002
```

자세한 환경 변수 설정은 [README-ENV.md](./README-ENV.md)를 참고하세요.

### 3. 개발 서버 실행

```bash
# 개발 모드 실행
npm run dev

# 또는 로컬 설정 우선 모드
npm run dev:local
```

### 4. 접속

애플리케이션이 실행되면 다음 URL로 접속할 수 있습니다:
- http://localhost:5173

## 백엔드 서비스 실행

프론트엔드가 정상적으로 작동하려면 다음 백엔드 서비스들이 실행되어야 합니다:

### Meta API (Java Backend) - 포트 8080
```bash
# oss-knowledge-backend 디렉토리에서
mvn spring-boot:run
```

### Embedding API (Python Backend) - 포트 8000
```bash
# oss-knowledge-embedding-back 디렉토리에서
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Search API (Python Backend) - 포트 8002
```bash
# oss-knowledge-search-back 디렉토리에서
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## 빌드

### 프로덕션 빌드
```bash
npm run build
```

### 로컬 빌드
```bash
npm run build:local
```

## 프로젝트 구조

```
src/
├── components/          # Vue 컴포넌트
├── views/              # 페이지 컴포넌트
├── services/           # API 서비스 모듈
│   ├── metaApi.js      # Meta API (Java Backend)
│   ├── embeddingApi.js # Embedding API (Python Backend)
│   ├── searchApi.js    # Search API (Python Backend)
│   └── index.js        # 통합 export
├── stores/             # Pinia 상태 관리
├── router/             # Vue Router 설정
└── utils/              # 유틸리티 함수
```

## 주요 기능

- **문서 관리**: Excel, Markdown 파일 업로드 및 처리
- **임베딩**: 문서 청킹 및 벡터 임베딩 생성
- **검색**: 의미 검색, 하이브리드 검색, Graph RAG
- **채팅**: RAG 기반 질의응답 시스템
- **부서 관리**: 부서별 문서 및 권한 관리
- **사용자 인증**: JWT 기반 인증 시스템

## 개발 가이드

자세한 개발 가이드와 환경 설정은 [README-ENV.md](./README-ENV.md)를 참고하세요.
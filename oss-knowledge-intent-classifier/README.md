# OSS Knowledge 의도 분류기

OSS Knowledge 시스템을 위한 FastAPI 기반 의도 분류 마이크로서비스입니다.

## 개요

이 서비스는 LangChain과 FastAPI를 사용하여 의도 분류 기능을 제공합니다. 사용자 쿼리를 분석하고 더 나은 라우팅과 처리를 위해 특정 의도로 분류하도록 설계되었습니다.

## 주요 기능

- **의도 분류**: 사용자 메시지를 GREETING, RAG_QUERY, OTHER로 분류
- **한국어 지원**: 한국어 패턴 매칭 및 프롬프트
- **검색 서버 연동**: RAG_QUERY 의도 시 검색 서버 호출
- **채팅 히스토리**: 대화 컨텍스트를 고려한 의도 분류
- **FastAPI 기반**: REST API 제공
- **Docker 지원**: 컨테이너화 지원
- **CORS 지원**: 크로스 오리진 요청 지원

## 의도 분류 시스템

### 지원하는 의도 유형

1. **GREETING**: 인사말
   - 예: "안녕", "안녕하세요", "좋은 아침"
   - 응답: 한국어 인사 응답

2. **RAG_QUERY**: 문서/지식베이스 검색 질문
   - 예: "인공지능이 무엇인지 설명해주세요", "API 문서를 보여주세요"
   - 응답: 검색 서버 연동을 통한 LLM 응답

3. **OTHER**: 기타 일반 대화
   - 예: "농담 해주세요", "오늘 날씨 어때?"
   - 응답: 한국어 모델을 통한 일반 응답

## 빠른 시작

### 로컬 개발

1. 의존성 설치:

```bash
pip install -r requirements.txt
```

2. 서버 실행:

```bash
python main.py
```

서버는 `http://localhost:8001`에서 사용 가능합니다.

### Docker

1. 이미지 빌드:

```bash
docker build -t oss-knowledge-intent-classifier .
```

2. 컨테이너 실행:

```bash
docker run -p 8001:8001 oss-knowledge-intent-classifier
```

## API 엔드포인트

### 채팅

- **POST** `/chat` - 의도 분류 및 응답 생성
  - 요청 본문:
    ```json
    {
      "message": "사용자 메시지",
      "user_id": "사용자 ID",
      "chat_history": [
        {"role": "user", "content": "이전 메시지"},
        {"role": "assistant", "content": "이전 응답"}
      ]
    }
    ```

### 헬스 체크

- **GET** `/health` - 서비스 상태 확인

### 루트

- **GET** `/` - 기본 서비스 정보

## 환경 변수

다음 환경 변수를 필요에 따라 설정하세요:

- `OPENAI_API_KEY` - LangChain 통합을 위한 OpenAI API 키
- `LOG_LEVEL` - 로깅 레벨 (기본값: INFO)
- `SEARCH_SERVER_URL` - 검색 서버 URL (기본값: http://localhost:8002)

## 아키텍처

### 의도 분류 플로우

```
사용자 메시지 → 의도 분류 → 의도별 라우팅:
├── GREETING → 한국어 인사 응답
├── RAG_QUERY → 검색 서버 → LLM 응답
└── OTHER → 한국어 모델 응답
```

### 주요 컴포넌트

- **IntentClassifier**: 의도 분류 로직
- **SearchClient**: 검색 서버 연동
- **Korean Prompts**: 한국어 프롬프트 관리
- **Pattern Matching**: 규칙 기반 분류

## 개발

이 서비스는 의도 분류 기능이 구현된 완전한 프레임워크입니다.

## 라이선스

OSS Knowledge 시스템의 일부입니다.
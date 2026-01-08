# Mem0 Azure Deployment

> 🧠 대화형 AI를 위한 장기 기억 시스템 - Azure 환경 최적화 버전

## 📖 프로젝트 개요

Mem0는 AI 대화 시스템에 **장기 기억**과 **개인화** 기능을 제공하는 오픈소스 메모리 엔진입니다. 이 프로젝트는 Mem0를 Azure 클라우드 환경에 맞게 최적화하여 배포하기 위한 설정을 포함합니다.

### 🎯 주요 기능

- **장기 기억 관리**: 사용자별 대화 히스토리와 맥락 정보를 장기간 저장
- **개인화**: 각 사용자의 선호도, 특성, 패턴을 학습하여 맞춤형 응답 제공
- **의미론적 검색**: 벡터 기반 유사도 검색으로 관련 기억 검색
- **메타데이터 지원**: 기억에 태그, 카테고리 등 추가 정보 저장
- **FastAPI 기반**: RESTful API를 통한 간단한 통합

### 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI API   │───▶│  Mem0 Engine    │
│  (채팅 시스템)    │    │    (REST API)   │    │  (메모리 관리)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                               ┌───────────────────────┼───────────────────────┐
                               │                       │                       │
                         ┌─────▼─────┐       ┌────────▼────────┐    ┌────────▼────────┐
                         │   Qdrant  │       │  Azure OpenAI   │    │   PostgreSQL    │
                         │ (벡터 DB)  │       │     (LLM)       │    │   (메타데이터)   │
                         └───────────┘       └─────────────────┘    └─────────────────┘
```

## 🚀 빠른 시작

### 1. 환경 변수 설정

```bash
# Azure OpenAI 설정
export AZURE_DEPLOYMENT="gpt-4.1-mini"
export AZURE_API_KEY="your-azure-openai-api-key"
export AZURE_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_API_VERSION="2024-02-15-preview"

# 데이터베이스 설정 (선택사항)
export POSTGRES_PASSWORD="your-postgres-password"
```

### 2. Docker Compose로 실행

```bash
# 개발 환경 실행
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f mem0-dev
```

### 3. API 테스트

```bash
# 서비스 상태 확인
curl http://localhost:8000/health

# 기억 추가
curl -X POST "http://localhost:8000/memory/add" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "사용자는 커피를 좋아하고 아침에 라떼를 마신다",
    "user_id": "user123",
    "metadata": {"category": "preference"}
  }'

# 기억 검색
curl -X POST "http://localhost:8000/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "사용자가 좋아하는 음료는?",
    "user_id": "user123"
  }'
```

## 📚 API 문서

서비스 실행 후 `http://localhost:8000/docs`에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

### 주요 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/` | 서비스 상태 확인 |
| `GET` | `/health` | 헬스 체크 |
| `POST` | `/memory/add` | 새로운 기억 추가 |
| `GET` | `/memory/get/{user_id}` | 사용자의 모든 기억 조회 |
| `POST` | `/memory/search` | 기억 검색 |

## 🔧 설정

### Vector Store (Qdrant)
- **호스트**: `20.249.165.27:6333`
- **컬렉션**: `mem0_collection`

### LLM (Azure OpenAI)
- **모델**: `gpt-4.1-mini`
- **온도**: 0.2
- **최대 토큰**: 1500

### 설정 파일
- `config/azure-config.yaml`: Mem0 메인 설정
- `config/secrets.yaml.template`: 시크릿 템플릿

## 🛠️ 개발 환경

### 로컬 개발

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
python src/main.py
```

### 주요 의존성
- `mem0ai>=0.1.117` - Mem0 코어 엔진
- `fastapi` - API 프레임워크
- `uvicorn` - ASGI 서버
- `azure-search-documents` - Azure Search 연동

## 🐳 Docker 배포

### 개발 환경
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 프로덕션 환경
```bash
# Dockerfile.azure 사용하여 빌드
docker build -f Dockerfile.azure -t mem0-azure .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env mem0-azure
```

## 🔍 사용 예시

### Python 클라이언트

```python
import requests

# 기억 추가
response = requests.post("http://localhost:8000/memory/add", json={
    "message": "사용자는 매일 오후 3시에 회의가 있다",
    "user_id": "user123",
    "metadata": {"type": "schedule"}
})

# 기억 검색
response = requests.post("http://localhost:8000/memory/search", json={
    "query": "사용자의 일정은?",
    "user_id": "user123"
})

memories = response.json()["results"]
```

### JavaScript 클라이언트

```javascript
// 기억 추가
const addMemory = async () => {
  const response = await fetch('http://localhost:8000/memory/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: "사용자는 한국어를 선호한다",
      user_id: "user123",
      metadata: { category: "language" }
    })
  });
  return await response.json();
};

// 기억 검색
const searchMemory = async () => {
  const response = await fetch('http://localhost:8000/memory/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: "사용자가 선호하는 언어는?",
      user_id: "user123"
    })
  });
  return await response.json();
};
```

## 🔐 보안

- 환경 변수를 통한 시크릿 관리
- Azure Key Vault 연동 권장 (프로덕션)
- API 키 및 엔드포인트 보안 설정

## 📝 로그 및 모니터링

```bash
# 실시간 로그 확인
docker-compose logs -f mem0-dev

# 특정 컨테이너 로그
docker logs -f <container_id>
```

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 Mem0 오픈소스 라이선스를 따릅니다.

## 🔗 관련 링크

- [Mem0 공식 문서](https://docs.mem0.ai/)
- [Mem0 GitHub](https://github.com/mem0ai/mem0)
- [Azure OpenAI 문서](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [Qdrant 문서](https://qdrant.tech/documentation/)

---

💡 **팁**: 대화형 AI 시스템에서 사용자별 맞춤형 경험을 제공하려면 Mem0를 통해 지속적으로 사용자의 선호도와 패턴을 학습시키는 것이 중요합니다.
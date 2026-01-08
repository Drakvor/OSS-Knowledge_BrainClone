# Mem0 업데이트 가이드

이 저장소는 [mem0ai/mem0](https://github.com/mem0ai/mem0)를 기반으로 하며, Azure 환경에 맞게 커스터마이징되어 있습니다.

## 📋 현재 커스터마이징된 파일들

다음 파일들은 프로젝트 전용 커스터마이징이 있으므로, 업데이트 시 주의가 필요합니다:

### 완전히 커스터마이징된 파일 (업데이트 시 보호 필요)
- `src/main.py` - FastAPI 엔드포인트 (Azure 전용)
- `src/embeddings/azure_openai.py` - Azure OpenAI embedding 지원
- `Dockerfile.azure` - Azure 배포용 Dockerfile
- `config/azure-config.yaml` - Azure 설정 파일
- `docker-compose.dev.yml` - 개발 환경 설정
- `README.md` - 프로젝트 문서

### 원본에서 가져와야 할 파일 (업데이트 시 병합 가능)
- `src/memory/` - 메모리 엔진 핵심 로직
- `src/vector_stores/` - 벡터 저장소 구현
- `src/configs/` - 설정 관련 코드
- `src/utils/` - 유틸리티 함수들
- 기타 라이브러리 코드

## 🔄 업데이트 방법

### 방법 1: Git Merge (권장)

원본 mem0의 변경사항을 병합하는 방법입니다.

```bash
# 1. upstream의 최신 변경사항 가져오기
git fetch upstream

# 2. 현재 브랜치 확인 (develop 또는 main)
git checkout develop

# 3. 업데이트할 버전 확인 (예: main 브랜치의 최신)
git log upstream/main --oneline -10

# 4. 특정 버전으로 병합 (예: 최신 main)
git merge upstream/main --no-commit --no-ff

# 5. 충돌 확인 및 해결
git status

# 6. 충돌이 있는 파일 확인 및 수정
# 주로 src/memory/, src/vector_stores/ 등의 파일에서 충돌 발생 가능

# 7. 커스터마이징된 파일 확인
# src/main.py, src/embeddings/azure_openai.py 등은 커스터마이징 유지

# 8. 충돌 해결 후 커밋
git add .
git commit -m "Merge upstream mem0 vX.X.X"
```

### 방법 2: Git Subtree (대안)

원본 저장소를 서브트리로 관리하는 방법입니다.

```bash
# 1. 서브트리 업데이트
git subtree pull --prefix=src upstream main --squash -m "Update mem0 subtree"

# 2. 충돌 해결 (필요시)
git status
```

### 방법 3: 선택적 파일 업데이트

특정 파일/디렉토리만 업데이트하는 방법입니다.

```bash
# 1. upstream의 최신 코드 가져오기
git fetch upstream

# 2. 특정 파일만 체크아웃 (예: vector_store 관련)
git checkout upstream/main -- src/vector_stores/qdrant.py

# 3. 변경사항 확인 및 커밋
git diff --cached
git commit -m "Update qdrant vector store from upstream"
```

## ⚠️ 주의사항

### 1. 백업 필수
업데이트 전에 반드시 백업을 생성하세요:

```bash
# 현재 브랜치 백업
git branch backup-before-update-$(date +%Y%m%d)

# 또는 원격에 푸시
git push origin develop
```

### 2. 충돌 해결 시 주의사항

충돌이 발생하면 다음을 확인하세요:

- **커스터마이징 파일**: `src/main.py`, `src/embeddings/azure_openai.py` 등은 Azure 전용 변경사항 유지
- **공통 파일**: `src/memory/`, `src/vector_stores/` 등은 원본 기능을 유지하면서 Azure 호환성 확인

### 3. 테스트 필수

업데이트 후 반드시 테스트를 수행하세요:

```bash
# 로컬 테스트
python src/main.py

# 또는 Docker로 테스트
docker-compose -f docker-compose.dev.yml up --build
```

## 📝 업데이트 체크리스트

- [ ] 현재 변경사항 커밋/스태시
- [ ] 백업 브랜치 생성
- [ ] upstream 최신 코드 가져오기
- [ ] 병합 실행
- [ ] 충돌 확인 및 해결
- [ ] 커스터마이징 파일 확인 (src/main.py, src/embeddings/azure_openai.py)
- [ ] 로컬 테스트
- [ ] 변경사항 커밋 및 푸시

## 🔍 업데이트 히스토리 확인

업데이트 내역을 확인하려면:

```bash
# upstream의 변경사항 확인
git log develop..upstream/main --oneline

# 특정 파일의 변경사항 확인
git diff develop upstream/main -- src/memory/main.py
```

## 📚 참고 자료

- [Mem0 공식 저장소](https://github.com/mem0ai/mem0)
- [Git Merge 가이드](https://git-scm.com/docs/git-merge)
- [Git Subtree 가이드](https://git-scm.com/book/en/v2/Git-Tools-Subtree-Merging)


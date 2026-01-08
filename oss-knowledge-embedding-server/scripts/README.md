# Scripts Directory

이 디렉토리는 OSS Knowledge Embedding Backend의 유지보수 및 관리 스크립트들을 포함합니다.

## 📁 스크립트 목록

### `recreate_collections.py`
PostgreSQL의 rag_departments 테이블을 기준으로 Qdrant 컬렉션들을 재생성하는 스크립트입니다.

**사용 시나리오:**
- Qdrant 컬렉션이 실수로 삭제된 경우
- 새로운 부서가 추가되어 컬렉션이 필요한 경우
- 시스템 초기 설정 시
- 데이터 동기화 문제 해결 시

## 🚀 사용법

### 방법 1: 쉘 스크립트 사용 (권장)
```bash
# embedding-back 디렉토리에서
./scripts/run_recreate.sh

# 강제 재생성
./scripts/run_recreate.sh --force
```

### 방법 2: 직접 Python 실행
```bash
# embedding-back 디렉토리에서

# 1. 신규 생성 (기존 컬렉션 건너뛰기)
python scripts/recreate_collections.py

# 2. 강제 재생성 (모든 기존 컬렉션 삭제 후 PostgreSQL 기반으로 재생성)
python scripts/recreate_collections.py --force
# 또는
python scripts/recreate_collections.py -f

# 3. 완전 초기화 (Qdrant 컬렉션 + PostgreSQL 문서 데이터 모두 삭제 후 재생성)
python scripts/recreate_collections.py --force --cleanup-postgresql
# 또는
python scripts/recreate_collections.py -f -cp

# 4. 부서별 문서 정리 (특정 부서의 문서만 삭제)
python scripts/recreate_collections.py --cleanup-postgresql
# 또는
python scripts/recreate_collections.py -cp
```

### 방법 3: 모듈로 실행
```bash
python -m scripts.recreate_collections
```

## 📋 실행 전 확인사항

1. **환경 설정 확인**
   - PostgreSQL 연결 정보가 올바른지 확인
   - Qdrant 서버가 실행 중인지 확인
   - 필요한 환경 변수들이 설정되어 있는지 확인

2. **데이터베이스 상태 확인**
   - `rag_departments` 테이블에 활성화된 부서들이 있는지 확인
   - PostgreSQL 서버가 정상 작동하는지 확인

## 📊 실행 결과

스크립트 실행 후 다음과 같은 정보를 제공합니다:

- ✅ 성공적으로 생성된 컬렉션 목록
- ❌ 생성에 실패한 컬렉션 목록  
- ⏭️ 이미 존재하여 건너뛴 컬렉션 목록
- 🔍 최종 Qdrant 컬렉션 상태

## 📝 로그 파일

실행 로그는 `scripts/collection_recreation.log` 파일에 저장됩니다.

## ⚠️ 주의사항

- **강제 재생성 모드** (`--force`) 사용 시 기존 컬렉션의 모든 데이터가 삭제됩니다
- 프로덕션 환경에서 실행하기 전에 반드시 백업을 확인하세요
- 스크립트 실행 중에는 다른 Qdrant 작업을 중단하는 것을 권장합니다

## 🔧 문제 해결

### 일반적인 오류들

1. **PostgreSQL 연결 실패**
   ```
   ❌ Failed to connect to PostgreSQL: connection timeout
   ```
   - PostgreSQL 서버 상태 확인
   - 연결 정보 (호스트, 포트, 인증 정보) 확인

2. **Qdrant 연결 실패**
   ```
   ❌ Failed to connect to Qdrant: connection refused
   ```
   - Qdrant 서버가 실행 중인지 확인
   - Qdrant 호스트/포트 설정 확인

3. **컬렉션 초기화 및 생성**
   - `--force` 옵션을 사용하여 기존 컬렉션 재생성
   - 또는 수동으로 컬렉션 삭제 후 재실행

## 📞 지원

문제가 발생하거나 추가 기능이 필요한 경우, 개발팀에 문의하세요.

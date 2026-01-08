# OSS Knowledge GitOps Repository

이 저장소는 OSS Knowledge Platform의 GitOps 기반 배포를 위한 Kubernetes 매니페스트들을 포함합니다.

## 🏗️ 구조

```
oss-knowledge-gitops/
├── front/                          # 프론트엔드 애플리케이션
│   ├── base/                      # 기본 매니페스트
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│   └── overlays/                  # 환경별 오버레이
│       ├── dev/                   # 개발 환경
│       └── prod/                  # 운영 환경
├── backend/                        # 백엔드 마이크로서비스들
│   ├── meta-api/                  # 메타 API 서비스
│   │   ├── base/
│   │   └── overlays/
│   ├── embedding-server/          # 임베딩 서버
│   │   ├── base/
│   │   └── overlays/
│   ├── search-server/             # 검색 서버
│   │   ├── base/
│   │   └── overlays/
│   ├── mem0/                      # Mem0 서비스
│   │   ├── base/
│   │   └── overlays/
│   └── overlays/                  # 공통 환경별 설정
│       ├── dev/                   # 개발 환경
│       └── prod/                  # 운영 환경
└── argocd-applications.yaml       # ArgoCD Application 정의
```

## 🚀 배포 방법

### 1. ArgoCD를 통한 자동 배포

이 저장소는 ArgoCD와 연동되어 있어 Git에 푸시하면 자동으로 배포됩니다.

#### 프론트엔드 배포
- **개발 환경**: `front/overlays/dev/`
- **운영 환경**: `front/overlays/prod/`

#### 백엔드 배포
- **Meta API**: `backend/meta-api/overlays/dev/` (개발), `backend/meta-api/overlays/prod/` (운영)
- **Embedding Server**: `backend/embedding-server/overlays/dev/` (개발), `backend/embedding-server/overlays/prod/` (운영)
- **Search Server**: `backend/search-server/overlays/dev/` (개발), `backend/search-server/overlays/prod/` (운영)
- **Mem0**: `backend/mem0/overlays/dev/` (개발)

### 2. 수동 배포

```bash
# 개발 환경 배포
kubectl apply -k front/overlays/dev/
kubectl apply -k backend/meta-api/overlays/dev/
kubectl apply -k backend/embedding-server/overlays/dev/
kubectl apply -k backend/search-server/overlays/dev/
kubectl apply -k backend/mem0/overlays/dev/

# 운영 환경 배포
kubectl apply -k front/overlays/prod/
kubectl apply -k backend/meta-api/overlays/prod/
kubectl apply -k backend/embedding-server/overlays/prod/
kubectl apply -k backend/search-server/overlays/prod/
```

## 🌐 접속 URL

### 프론트엔드
- **개발 환경**: http://oss-knowledge-front-dev.4.230.158.187.nip.io
- **운영 환경**: http://oss-knowledge-front.4.230.158.187.nip.io

### 백엔드
- **개발 환경**: `oss-knowledge-backend-dev` 네임스페이스
- **운영 환경**: `oss-knowledge-backend-prod` 네임스페이스

## 🔧 새로운 마이크로서비스 추가 방법

백엔드에 새로운 마이크로서비스를 추가하려면:

1. `backend/` 디렉토리에 새 서비스 폴더 생성
2. 각 서비스 폴더에 `base/` 및 `overlays/` 구조 생성
3. 필요한 Kubernetes 매니페스트 추가 (deployment, service, ingress 등)
4. `argocd-applications.yaml`에 새 ArgoCD Application 추가

### 예시: 새로운 서비스 추가
```
backend/
├── meta-api/                    # 기존 서비스
├── embedding-server/            # 기존 서비스  
├── search-server/               # 기존 서비스
├── mem0/                        # 기존 서비스
└── new-service/                 # 새로운 서비스
    ├── base/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── ingress.yaml
    │   └── kustomization.yaml
    └── overlays/
        ├── dev/
        └── prod/
```

## 📋 현재 배포된 서비스

- ✅ **프론트엔드**: Vue.js 기반 웹 애플리케이션
- ✅ **Meta API**: Java Spring Boot 기반 메타데이터 관리 API
- ✅ **Embedding Server**: Python FastAPI 기반 문서 임베딩 서버
- ✅ **Search Server**: Python FastAPI 기반 검색 서버
- ✅ **Mem0**: AI 메모리 관리 서버
- ✅ **ArgoCD Application**: 모든 서비스 자동 배포 설정 완료
- ✅ **개발/운영 환경 분리**: 완전 분리된 환경 구성

## 🚧 향후 개선 사항

1. 모니터링 및 로깅 설정 추가 (Prometheus, Grafana, ELK Stack)
2. 보안 정책 및 네트워크 정책 강화
3. 서비스 메시 도입 (Istio 등)
4. 백업 및 재해복구 전략 수립

## 📞 문의

GitOps 관련 문의사항이 있으시면 개발팀에 연락해주세요.

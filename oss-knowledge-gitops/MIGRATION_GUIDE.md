# 🚀 OSS Knowledge GitOps 마이그레이션 가이드

이 문서는 기존 `java-api` 구조에서 새로운 `oss-knowledge-meta-api` 구조로 마이그레이션하기 위한 단계별 가이드입니다.

## 📋 마이그레이션 개요

### 변경 사항
- **구조 변경**: `apps/java-api/` → `backend/meta-api/`
- **서비스명 변경**: `java-api` → `oss-knowledge-meta-api`
- **네임스페이스 변경**: `java-api-dev` → `oss-knowledge-backend-dev`
- **ArgoCD App 변경**: `java-api-dev` → `oss-knowledge-meta-api-dev`

## 🗂️ 1. 기존 리소스 정리

### 1.1 기존 네임스페이스 및 리소스 확인
```bash
# 기존 네임스페이스 확인
kubectl get namespaces | grep java-api

# 기존 ArgoCD 애플리케이션 확인
kubectl get applications -n argocd | grep java-api

# 기존 Pod 및 서비스 확인
kubectl get all -n java-api-dev
```

### 1.2 기존 데이터 백업 (필요시)
```bash
# 기존 ConfigMap 백업
kubectl get configmap -n java-api-dev -o yaml > backup-configmaps.yaml

# 기존 Secret 백업 (주의: 민감정보 포함)
kubectl get secret -n java-api-dev -o yaml > backup-secrets.yaml

# 기존 PVC 확인 (데이터 유지 필요한 경우)
kubectl get pvc -n java-api-dev
```

### 1.3 기존 ArgoCD 애플리케이션 삭제
```bash
# ArgoCD 애플리케이션 삭제 (리소스 함께 삭제)
kubectl delete application java-api-dev -n argocd

# 또는 ArgoCD UI에서 삭제:
# http://argocd.4.230.158.187.nip.io
# Applications → java-api-dev → DELETE
```

### 1.4 기존 네임스페이스 정리
```bash
# 네임스페이스 삭제 (모든 리소스 함께 삭제)
kubectl delete namespace java-api-dev

# 네임스페이스가 Terminating 상태에서 멈춘 경우
kubectl get namespace java-api-dev -o json > temp-ns.json
# temp-ns.json에서 finalizers 배열을 비우고
kubectl replace --raw "/api/v1/namespaces/java-api-dev/finalize" -f temp-ns.json
```

## 🔧 2. Jenkins 재구성

### 2.1 Jenkins 파이프라인 업데이트
기존 Jenkins Job의 파이프라인 설정을 다음과 같이 업데이트:

```groovy
// Repository URL 변경 (필요시)
// Git Repository: oss-knowledge-backend (기존과 동일)
// Branch: main

// Pipeline Script Path
// devops/Jenkinsfile (기존과 동일 - 이미 업데이트됨)
```

### 2.2 Jenkins 환경변수 확인
다음 환경변수들이 올바르게 설정되었는지 확인:
- `DOCKER_REGISTRY`: `ossknowledgeregistry.azurecr.io`
- `IMAGE_NAME`: `oss-knowledge-meta-api` (업데이트됨)
- `NAMESPACE`: `oss-knowledge-backend-dev` (업데이트됨)
- `ARGOCD_APP_NAME`: `oss-knowledge-meta-api-dev` (업데이트됨)

### 2.3 Jenkins Credential 확인
다음 자격증명이 설정되어 있는지 확인:
- `acr-credential`: Azure Container Registry 접근용
- `gitlab-token`: GitOps 레포지토리 업데이트용

## 🏗️ 3. ArgoCD 재구성

### 3.1 새로운 ArgoCD 애플리케이션 생성

#### 방법 1: ArgoCD UI 사용
1. ArgoCD UI 접속: http://argocd.4.230.158.187.nip.io
2. "NEW APP" 클릭
3. 다음 정보 입력:
   ```
   Application Name: oss-knowledge-meta-api-dev
   Project: default
   Sync Policy: Automatic
   
   Repository URL: https://gitlab.4.230.158.187.nip.io/oss-ai-vtf/oss-knowledge-gitops.git
   Revision: HEAD
   Path: backend/meta-api/overlays/dev
   
   Cluster URL: https://kubernetes.default.svc
   Namespace: oss-knowledge-backend-dev
   ```

#### 방법 2: kubectl 사용
```bash
# ArgoCD 애플리케이션 생성
kubectl apply -f argocd-applications.yaml

# 또는 직접 생성
cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: oss-knowledge-meta-api-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://gitlab.4.230.158.187.nip.io/oss-ai-vtf/oss-knowledge-gitops.git
    targetRevision: HEAD
    path: backend/meta-api/overlays/dev
  destination:
    server: https://kubernetes.default.svc
    namespace: oss-knowledge-backend-dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

### 3.2 동기화 확인
```bash
# ArgoCD 애플리케이션 상태 확인
kubectl get application oss-knowledge-meta-api-dev -n argocd

# 동기화 상태 확인
kubectl describe application oss-knowledge-meta-api-dev -n argocd

# 수동 동기화 (필요시)
kubectl patch application oss-knowledge-meta-api-dev -n argocd \
  --type='merge' -p='{"operation":{"sync":{}}}'
```

## 🔍 4. 배포 확인

### 4.1 새로운 리소스 확인
```bash
# 새로운 네임스페이스 확인
kubectl get namespace oss-knowledge-backend-dev

# 배포된 리소스 확인
kubectl get all -n oss-knowledge-backend-dev

# Pod 로그 확인
kubectl logs -n oss-knowledge-backend-dev deployment/oss-knowledge-meta-api

# 서비스 상태 확인
kubectl get svc -n oss-knowledge-backend-dev
kubectl get ingress -n oss-knowledge-backend-dev
```

### 4.2 헬스체크
```bash
# 애플리케이션 헬스체크
curl -I http://oss-knowledge-meta-api-dev.4.230.158.187.nip.io/healthz

# 또는 Pod 내부에서 확인
kubectl exec -n oss-knowledge-backend-dev deployment/oss-knowledge-meta-api -- curl localhost:8080/healthz
```

## 🚨 5. 트러블슈팅

### 5.1 일반적인 문제들

#### ArgoCD 동기화 실패
```bash
# ArgoCD 애플리케이션 재시작
kubectl delete application oss-knowledge-meta-api-dev -n argocd
kubectl apply -f argocd-applications.yaml

# GitOps 레포지토리 권한 확인
# GitLab에서 Deploy Token 또는 Access Token 재생성
```

#### Pod 시작 실패
```bash
# 이벤트 확인
kubectl describe pod -n oss-knowledge-backend-dev

# 이미지 풀 확인
kubectl get events -n oss-knowledge-backend-dev --sort-by='.lastTimestamp'

# Secret 확인
kubectl get secret -n oss-knowledge-backend-dev
kubectl describe secret oss-knowledge-meta-api-secret -n oss-knowledge-backend-dev
```

#### 네트워크 연결 문제
```bash
# DNS 해상도 확인
nslookup oss-knowledge-meta-api-dev.4.230.158.187.nip.io

# Ingress Controller 확인
kubectl get pods -n ingress-nginx

# Service Endpoints 확인
kubectl get endpoints -n oss-knowledge-backend-dev
```

### 5.2 롤백 절차 (긴급시)

#### 1단계: ArgoCD 애플리케이션 일시 중지
```bash
kubectl patch application oss-knowledge-meta-api-dev -n argocd \
  --type='merge' -p='{"spec":{"syncPolicy":null}}'
```

#### 2단계: 기존 백업으로 복원
```bash
# 기존 네임스페이스 재생성
kubectl create namespace java-api-dev

# 백업된 리소스 복원
kubectl apply -f backup-configmaps.yaml
kubectl apply -f backup-secrets.yaml
```

#### 3단계: 기존 이미지로 임시 배포
```bash
# 임시 Deployment 생성
kubectl create deployment java-api --image=ossknowledgeregistry.azurecr.io/java-api:latest -n java-api-dev
kubectl expose deployment java-api --port=80 --target-port=8080 -n java-api-dev
```

## 📊 6. 성능 및 모니터링

### 6.1 리소스 사용량 확인
```bash
# CPU/Memory 사용량 확인
kubectl top pods -n oss-knowledge-backend-dev
kubectl top nodes

# HPA 설정 (필요시)
kubectl autoscale deployment oss-knowledge-meta-api -n oss-knowledge-backend-dev \
  --cpu-percent=70 --min=2 --max=10
```

### 6.2 로그 모니터링
```bash
# 실시간 로그 확인
kubectl logs -f -n oss-knowledge-backend-dev deployment/oss-knowledge-meta-api

# 최근 로그 확인
kubectl logs --tail=100 -n oss-knowledge-backend-dev deployment/oss-knowledge-meta-api
```

## ✅ 7. 마이그레이션 체크리스트

### 사전 준비
- [ ] 기존 리소스 백업 완료
- [ ] Jenkins Credential 확인
- [ ] GitOps 레포지토리 접근 권한 확인
- [ ] ACR 이미지 접근 권한 확인

### 마이그레이션 실행
- [ ] 기존 ArgoCD 애플리케이션 삭제
- [ ] 기존 네임스페이스 정리
- [ ] Jenkins 파이프라인 실행
- [ ] 새로운 ArgoCD 애플리케이션 생성
- [ ] 동기화 확인

### 사후 확인
- [ ] 새로운 서비스 정상 동작 확인
- [ ] 헬스체크 통과
- [ ] 로그 정상 출력
- [ ] 데이터베이스 연결 확인
- [ ] 프론트엔드 연동 확인

## 📞 지원 정보

### 유용한 명령어 모음
```bash
# 전체 상태 한눈에 보기
kubectl get all,ingress,pvc,secrets,configmaps -n oss-knowledge-backend-dev

# ArgoCD 애플리케이션 상태 확인
kubectl get applications -n argocd -o wide

# 클러스터 전체 리소스 확인
kubectl get nodes
kubectl get namespaces
kubectl cluster-info
```

### 접속 URL 정리
- **ArgoCD**: http://argocd.4.230.158.187.nip.io
- **개발환경 API**: http://oss-knowledge-meta-api-dev.4.230.158.187.nip.io
- **운영환경 API**: http://oss-knowledge-meta-api.4.230.158.187.nip.io
- **프론트엔드 개발**: http://oss-knowledge-front-dev.4.230.158.187.nip.io

---

**⚠️ 주의사항:**
1. 운영환경 작업 전에 반드시 개발환경에서 먼저 테스트
2. 데이터베이스 마이그레이션이 필요한 경우 별도 계획 수립
3. 롤백 계획을 미리 준비하고 팀원들과 공유
4. 마이그레이션 중 서비스 중단 시간 최소화

**🎯 마이그레이션 성공 기준:**
- 새로운 구조로 정상 배포
- 기존 기능 모두 정상 동작
- 데이터 손실 없음
- CI/CD 파이프라인 정상 동작
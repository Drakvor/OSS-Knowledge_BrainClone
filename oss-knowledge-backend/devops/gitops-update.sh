#!/usr/bin/env bash
# GitOps 리포지토리 이미지 태그 갱신 및 ArgoCD 동기화
# 사용법: ./gitops-update.sh <gitops_repo_url> <branch> <manifest_path> <app_name> <new_tag>
# 필요 환경변수: GITLAB_TOKEN, ARGOCD_SERVER, ARGOCD_TOKEN
set -euo pipefail

if [ "$#" -ne 5 ]; then
  echo '{"level":"error","msg":"usage: repo_url branch manifest_path app_name tag","ts":"'$(date -u +%FT%TZ)'"}' >&2
  exit 1
fi

REPO_URL="$1"
BRANCH="$2"
MANIFEST_PATH="$3"
APP_NAME="$4"
NEW_TAG="$5"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$TMP_DIR"
GIT_ASKPASS=/bin/true git clone -b "$BRANCH" "https://oauth2:${GITLAB_TOKEN}@${REPO_URL#https://}" repo
cd repo
# 이미지 태그 변경 (단순 sed 예시)
sed -i "s|image: \(.*:\).*|image: \1${NEW_TAG}|" "$MANIFEST_PATH"

git config user.name "gitops-bot"
git config user.email "gitops-bot@example.com"
git commit -am "chore: update image tag to ${NEW_TAG}"
git push origin "$BRANCH"

argocd login "$ARGOCD_SERVER" --sso --grpc-web --auth-token "$ARGOCD_TOKEN"
argocd app sync --grpc-web "$APP_NAME"

echo '{"level":"info","msg":"gitops updated","ts":"'$(date -u +%FT%TZ)'"}'

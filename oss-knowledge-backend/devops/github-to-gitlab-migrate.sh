#!/usr/bin/env bash
# Github → Gitlab 미러링 스크립트
# 사용법: ./github-to-gitlab-migrate.sh <github_repo_url> <gitlab_repo_url>
# 토큰은 환경변수 GITHUB_TOKEN, GITLAB_TOKEN 사용
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo '{"level":"error","msg":"usage: github_url gitlab_url","ts":"'$(date -u +%FT%TZ)'"}' >&2
  exit 1
fi

GITHUB_URL="$1"
GITLAB_URL="$2"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$TMP_DIR"
# Github 클론
GIT_ASKPASS=/bin/true git clone --mirror "https://oauth2:${GITHUB_TOKEN}@${GITHUB_URL#https://}" repo
cd repo
# Gitlab에 푸시
GIT_ASKPASS=/bin/true git push --mirror "https://oauth2:${GITLAB_TOKEN}@${GITLAB_URL#https://}"

echo '{"level":"info","msg":"migration complete","ts":"'$(date -u +%FT%TZ)'"}'

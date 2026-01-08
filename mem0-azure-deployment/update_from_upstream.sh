#!/bin/bash
# mem0 업데이트 스크립트
# 사용법: ./update_from_upstream.sh [브랜치명]
# 예: ./update_from_upstream.sh main

set -e  # 에러 발생 시 중단

BRANCH=${1:-main}  # 기본값: main
CURRENT_BRANCH=$(git branch --show-current)
BACKUP_BRANCH="backup-before-update-$(date +%Y%m%d-%H%M%S)"

echo "🔍 Mem0 업데이트 시작..."
echo "─────────────────────────────────────────"
echo "현재 브랜치: $CURRENT_BRANCH"
echo "업데이트할 upstream 브랜치: $BRANCH"
echo "백업 브랜치: $BACKUP_BRANCH"
echo "─────────────────────────────────────────"
echo "⚠️  현재 브랜치($CURRENT_BRANCH)에서 업데이트를 진행합니다."
echo "   다른 브랜치를 사용하려면 먼저 해당 브랜치로 전환하세요."
echo "─────────────────────────────────────────"

# 1. 변경사항 확인
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  커밋되지 않은 변경사항이 있습니다."
    echo "다음 중 선택하세요:"
    echo "1) 커밋하기"
    echo "2) 스태시하기"
    echo "3) 취소하기"
    read -p "선택 (1/2/3): " choice
    
    case $choice in
        1)
            git add .
            read -p "커밋 메시지: " commit_msg
            git commit -m "$commit_msg"
            ;;
        2)
            git stash push -m "Stash before update - $BACKUP_BRANCH"
            ;;
        3)
            echo "취소되었습니다."
            exit 1
            ;;
        *)
            echo "잘못된 선택입니다."
            exit 1
            ;;
    esac
fi

# 2. 백업 브랜치 생성
echo ""
echo "📦 백업 브랜치 생성: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"
echo "✅ 백업 완료"

# 3. upstream 최신 코드 가져오기
echo ""
echo "📥 upstream 최신 코드 가져오기..."
git fetch upstream

# 4. 현재 브랜치 확인
if [ "$CURRENT_BRANCH" = "HEAD" ]; then
    echo "⚠️  Detached HEAD 상태입니다. 브랜치를 확인하세요."
    exit 1
fi

# 5. 업데이트할 커밋 확인
echo ""
echo "📋 업데이트할 커밋 목록:"
git log "$CURRENT_BRANCH..upstream/$BRANCH" --oneline -10 || echo "   (변경사항 없음)"

# 6. 사용자 확인
echo ""
read -p "업데이트를 진행하시겠습니까? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "취소되었습니다."
    exit 0
fi

# 7. 병합 실행
echo ""
echo "🔄 병합 실행 중..."

# 관계 없는 히스토리 병합 허용 (처음 업데이트하는 경우)
MERGE_CMD="git merge upstream/$BRANCH --no-edit --allow-unrelated-histories"

if $MERGE_CMD; then
    echo "✅ 병합 완료! 충돌 없이 업데이트되었습니다."
else
    MERGE_STATUS=$?
    echo "⚠️  병합 중 문제가 발생했습니다."
    
    # 충돌 확인
    if git status --short | grep -q "^UU"; then
        echo "충돌이 발생했습니다. 다음 파일들을 확인하세요:"
        git status --short | grep "^UU"
        echo ""
        echo "충돌 해결 후 다음 명령어를 실행하세요:"
        echo "  git add ."
        echo "  git commit"
    else
        echo "다른 문제가 발생했습니다. 상태를 확인하세요:"
        git status
    fi
    exit $MERGE_STATUS
fi

# 8. 커스터마이징 파일 확인
echo ""
echo "🔍 커스터마이징 파일 확인:"
CUSTOM_FILES=(
    "src/main.py"
    "src/embeddings/azure_openai.py"
    "Dockerfile.azure"
    "config/azure-config.yaml"
)

for file in "${CUSTOM_FILES[@]}"; do
    if git diff "$BACKUP_BRANCH" HEAD -- "$file" | grep -q "^+"; then
        echo "⚠️  $file - 변경사항 발견 (확인 필요)"
    else
        echo "✅ $file - 변경사항 없음"
    fi
done

echo ""
echo "✨ 업데이트 완료!"
echo ""
echo "다음 단계:"
echo "1. 코드 검토 및 테스트"
echo "2. 테스트 후 문제없으면 푸시: git push origin $CURRENT_BRANCH"
echo "3. 문제가 있으면 백업에서 복구: git reset --hard $BACKUP_BRANCH"


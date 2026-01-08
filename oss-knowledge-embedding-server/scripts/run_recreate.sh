#!/bin/bash
"""
Qdrant 컬렉션 재생성 스크립트 실행기
===================================

이 스크립트는 올바른 환경에서 recreate_collections.py를 실행합니다.
"""

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")/.."

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo "🔧 Activating virtual environment..."
    source ../venv/bin/activate
fi

# 환경 변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: No .env file found in $(pwd)"
    echo "   Make sure your environment variables are set correctly."
fi

# 스크립트 실행
echo "🚀 Running collection recreation script..."
echo "=========================================="

if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
    echo "🔄 Force recreate mode enabled"
    python scripts/recreate_collections.py --force
else
    python scripts/recreate_collections.py
fi

echo "=========================================="
echo "✅ Script execution completed!"

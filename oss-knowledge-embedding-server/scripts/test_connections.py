#!/usr/bin/env python3
"""
연결 테스트 스크립트
==================

PostgreSQL과 Qdrant 연결 상태를 확인하는 간단한 테스트 스크립트입니다.
recreate_collections.py 실행 전에 연결 상태를 확인할 때 사용하세요.

사용법:
    python scripts/test_connections.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment variables from {env_file}")
else:
    print("⚠️  No .env file found. Using system environment variables.")

import psycopg2
from qdrant_client import QdrantClient
from app.config import settings


def test_postgresql():
    """PostgreSQL 연결 테스트"""
    print("🔍 Testing PostgreSQL connection...")
    
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DATABASE,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rag_departments WHERE status = 'active'")
        active_departments = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ PostgreSQL connection successful!")
        print(f"   📊 Active departments: {active_departments}")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


def test_qdrant():
    """Qdrant 연결 테스트"""
    print("\n🔍 Testing Qdrant connection...")
    
    try:
        if settings.QDRANT_API_KEY:
            client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
                https=settings.QDRANT_HTTPS
            )
        else:
            client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
        
        collections = client.get_collections()
        collection_count = len(collections.collections)
        
        print(f"✅ Qdrant connection successful!")
        print(f"   📦 Existing collections: {collection_count}")
        
        if collection_count > 0:
            print("   📋 Collection names:")
            for col in collections.collections:
                print(f"      - {col.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("🧪 Connection Test Script")
    print("=" * 40)
    
    postgres_ok = test_postgresql()
    qdrant_ok = test_qdrant()
    
    print("\n" + "=" * 40)
    print("📋 Test Summary:")
    print(f"   PostgreSQL: {'✅ OK' if postgres_ok else '❌ FAIL'}")
    print(f"   Qdrant: {'✅ OK' if qdrant_ok else '❌ FAIL'}")
    
    if postgres_ok and qdrant_ok:
        print("\n🎉 All connections are working! You can run recreate_collections.py")
        return 0
    else:
        print("\n💥 Some connections failed. Please check your configuration.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Qdrant 컬렉션 재생성 스크립트
================================

PostgreSQL의 rag_departments 테이블을 기준으로 Qdrant 컬렉션들을 재생성합니다.
이 스크립트는 다음과 같은 상황에서 유용합니다:

1. Qdrant 컬렉션이 실수로 삭제된 경우
2. 새로운 부서가 추가되어 컬렉션이 필요한 경우  
3. 시스템 초기 설정 시
4. 데이터 동기화 문제 해결 시

사용법:
    python scripts/recreate_collections.py

또는:
    cd oss-knowledge-embedding-back
    python -m scripts.recreate_collections
"""

import asyncio
import logging
import sys
import os
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

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, CreateCollection
import psycopg2
from app.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(Path(__file__).parent / 'collection_recreation.log'))
    ]
)
logger = logging.getLogger(__name__)


class CollectionRecreator:
    """Qdrant 컬렉션 재생성 클래스"""
    
    def __init__(self):
        self.postgres_conn = None
        self.qdrant_client = None
        
    def connect_postgres(self):
        """PostgreSQL 연결"""
        try:
            self.postgres_conn = psycopg2.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DATABASE,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                connect_timeout=10
            )
            logger.info(f"✅ Connected to PostgreSQL at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
    
    def connect_qdrant(self):
        """Qdrant 연결"""
        try:
            if settings.QDRANT_API_KEY:
                self.qdrant_client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    https=settings.QDRANT_HTTPS
                )
            else:
                self.qdrant_client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT
                )
            
            # 연결 테스트
            self.qdrant_client.get_collections()
            logger.info(f"✅ Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False
    
    def get_departments(self):
        """PostgreSQL에서 활성화된 부서 목록 조회"""
        try:
            cursor = self.postgres_conn.cursor()
            
            # 활성화된 부서들 조회
            cursor.execute("""
                SELECT id, name, description, status, created_at
                FROM rag_departments 
                WHERE status = 'active' 
                ORDER BY id
            """)
            
            departments = cursor.fetchall()
            cursor.close()
            
            logger.info(f"📋 Found {len(departments)} active departments in PostgreSQL")
            
            # 부서 정보 출력
            for dept in departments:
                logger.info(f"  - ID: {dept[0]}, Name: '{dept[1]}', Description: '{dept[2]}'")
            
            return departments
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch departments from PostgreSQL: {e}")
            return []
    
    def get_existing_collections(self):
        """Qdrant에서 기존 컬렉션 목록 조회"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            logger.info(f"📦 Found {len(collection_names)} existing collections in Qdrant")
            for name in collection_names:
                logger.info(f"  - {name}")
            
            return collection_names
            
        except Exception as e:
            logger.error(f"❌ Failed to get existing collections from Qdrant: {e}")
            return []
    
    def create_collection(self, collection_name, department_name):
        """단일 컬렉션 생성"""
        try:
            # 컬렉션 생성
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=3072,  # OpenAI text-embedding-3-large dimension
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"✅ Created collection '{collection_name}' for department '{department_name}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection '{collection_name}' for '{department_name}': {e}")
            return False
    
    def delete_collection(self, collection_name):
        """단일 컬렉션 삭제"""
        try:
            self.qdrant_client.delete_collection(collection_name)
            logger.info(f"🗑️  Deleted existing collection: {collection_name}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Failed to delete collection '{collection_name}': {e}")
            return False
    
    def cleanup_postgresql_documents(self, department_ids=None):
        """PostgreSQL의 문서 메타데이터 정리"""
        if department_ids:
            logger.info(f"🗑️  Cleaning up PostgreSQL document metadata for departments: {department_ids}")
        else:
            logger.info("🗑️  Cleaning up ALL PostgreSQL document metadata...")
        
        try:
            cursor = self.postgres_conn.cursor()
            
            # 부서별 문서 삭제 또는 전체 삭제
            if department_ids:
                # 특정 부서들의 문서만 삭제
                placeholders = ','.join(['%s'] * len(department_ids))
                cursor.execute(f"DELETE FROM document_metadata WHERE department_id IN ({placeholders})", department_ids)
                deleted_docs = cursor.rowcount
                logger.info(f"   - Deleted {deleted_docs} document metadata records for departments {department_ids}")
            else:
                # 모든 문서 삭제
                cursor.execute("DELETE FROM document_metadata")
                deleted_docs = cursor.rowcount
                logger.info(f"   - Deleted {deleted_docs} document metadata records (all departments)")
            
            # 문서-카테고리 연결 삭제 (삭제된 문서와 연결된 것들)
            cursor.execute("DELETE FROM document_category_links WHERE document_id NOT IN (SELECT id FROM document_metadata)")
            deleted_links = cursor.rowcount
            
            # 문서-부서 연결 삭제 (있다면)
            try:
                cursor.execute("DELETE FROM document_department_links WHERE document_id NOT IN (SELECT id FROM document_metadata)")
                deleted_dept_links = cursor.rowcount
            except Exception:
                deleted_dept_links = 0
                logger.info("⚠️  document_department_links table not found, skipping")
            
            self.postgres_conn.commit()
            cursor.close()
            
            logger.info(f"🗑️  PostgreSQL cleanup completed:")
            logger.info(f"   - Deleted {deleted_links} orphaned document-category links")
            logger.info(f"   - Deleted {deleted_dept_links} orphaned document-department links")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup PostgreSQL documents: {e}")
            return False

    def recreate_all_collections(self, force_recreate=False, cleanup_postgresql=False):
        """모든 컬렉션 재생성"""
        logger.info("🚀 Starting collection recreation process...")
        
        # 연결 확인
        if not self.connect_postgres():
            return False
        if not self.connect_qdrant():
            return False
        
        # 부서 목록 조회
        departments = self.get_departments()
        if not departments:
            logger.error("❌ No departments found. Aborting.")
            return False
        
        # 기존 컬렉션 목록 조회
        existing_collections = self.get_existing_collections()
        
        # 강제 재생성 모드: 모든 기존 컬렉션 삭제
        if force_recreate:
            logger.info("🗑️  Force recreate mode: Deleting ALL existing collections...")
            deleted_count = 0
            for collection_name in existing_collections:
                if collection_name != 'general':  # general 컬렉션은 보존
                    try:
                        self.qdrant_client.delete_collection(collection_name)
                        logger.info(f"🗑️  Deleted collection: {collection_name}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to delete collection '{collection_name}': {e}")
            logger.info(f"🗑️  Deleted {deleted_count} existing collections")
            
            # PostgreSQL 문서 데이터 정리 (옵션)
            if cleanup_postgresql:
                # 삭제된 부서들의 문서도 함께 정리
                deleted_department_ids = []
                for dept_id, dept_name, dept_description, dept_status, created_at in departments:
                    collection_name = dept_name
                    if collection_name in existing_collections:
                        deleted_department_ids.append(dept_id)
                
                if deleted_department_ids:
                    logger.info(f"🗑️  Also cleaning up documents for recreated departments: {deleted_department_ids}")
                    self.cleanup_postgresql_documents(deleted_department_ids)
                else:
                    logger.info("🗑️  No department documents to clean up (all collections are new)")
        
        # 결과 추적
        created_collections = []
        failed_collections = []
        skipped_collections = []
        
        # 각 부서별 컬렉션 생성
        for dept_id, dept_name, dept_description, dept_status, created_at in departments:
            # 부서 이름을 그대로 컬렉션 이름으로 사용
            collection_name = dept_name
            
            # 강제 재생성 모드가 아니고 이미 존재하는 컬렉션 처리
            if not force_recreate and collection_name in existing_collections:
                logger.info(f"⏭️  Skipping existing collection '{collection_name}' for '{dept_name}'")
                skipped_collections.append({
                    'id': dept_id,
                    'name': dept_name,
                    'collection': collection_name
                })
                continue
            
            # 새 컬렉션 생성
            if self.create_collection(collection_name, dept_name):
                created_collections.append({
                    'id': dept_id,
                    'name': dept_name,
                    'collection': collection_name
                })
            else:
                failed_collections.append({
                    'id': dept_id,
                    'name': dept_name,
                    'collection': collection_name
                })
        
        # 결과 요약 출력
        self.print_summary(created_collections, failed_collections, skipped_collections)
        
        # 최종 컬렉션 목록 확인
        self.verify_final_state()
        
        return len(failed_collections) == 0
    
    def print_summary(self, created, failed, skipped):
        """결과 요약 출력"""
        logger.info("\n" + "="*60)
        logger.info("🎯 COLLECTION RECREATION SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Successfully created: {len(created)} collections")
        logger.info(f"❌ Failed to create: {len(failed)} collections")
        logger.info(f"⏭️  Skipped (already exist): {len(skipped)} collections")
        
        if created:
            logger.info("\n📦 Created collections:")
            for col in created:
                logger.info(f"  ✅ Collection '{col['collection']}' for department '{col['name']}' (ID: {col['id']})")
        
        if failed:
            logger.info("\n❌ Failed collections:")
            for col in failed:
                logger.info(f"  ❌ Collection '{col['collection']}' for department '{col['name']}'")
        
        if skipped:
            logger.info("\n⏭️  Skipped collections:")
            for col in skipped:
                logger.info(f"  ⏭️  Collection '{col['collection']}' for department '{col['name']}' (already exists)")
    
    def verify_final_state(self):
        """최종 상태 확인"""
        try:
            final_collections = self.qdrant_client.get_collections()
            final_names = [col.name for col in final_collections.collections]
            
            logger.info(f"\n🔍 Final Qdrant collections ({len(final_names)} total):")
            for name in sorted(final_names, key=lambda x: int(x) if x.isdigit() else 999):
                logger.info(f"  📦 {name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to verify final state: {e}")
    
    def close_connections(self):
        """연결 종료"""
        if self.postgres_conn:
            self.postgres_conn.close()
            logger.info("🔌 Closed PostgreSQL connection")


def main():
    """메인 실행 함수"""
    logger.info("🎬 Starting Qdrant Collection Recreation Script")
    logger.info("="*60)
    
    # 명령행 인수 확인
    force_recreate = "--force" in sys.argv or "-f" in sys.argv
    cleanup_postgresql = "--cleanup-postgresql" in sys.argv or "-cp" in sys.argv
    
    if force_recreate:
        logger.info("🔄 Force recreate mode enabled - existing collections will be recreated")
    
    if cleanup_postgresql:
        logger.info("🗑️  PostgreSQL cleanup mode enabled - document metadata will be deleted")
    
    # 재생성 실행
    recreator = CollectionRecreator()
    
    try:
        success = recreator.recreate_all_collections(
            force_recreate=force_recreate, 
            cleanup_postgresql=cleanup_postgresql
        )
        
        if success:
            logger.info("\n🎉 Collection recreation completed successfully!")
            return 0
        else:
            logger.error("\n💥 Collection recreation completed with errors!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Process interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n💥 Unexpected error: {e}")
        return 1
    finally:
        recreator.close_connections()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

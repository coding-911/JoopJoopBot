import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import pytest
import psycopg2
from psycopg2.extras import DictCursor

from joopjoop.dart import DartClient, DartCollector
from joopjoop.rag import RAGPipeline
from tests.dart.models_for_test import DartReport

# 프로젝트 루트 디렉토리 찾기
def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current.name != "JoopJoopBot" and current.parent != current:
        current = current.parent
    return current

# 환경변수 로드
project_root = find_project_root()
load_dotenv(project_root / ".env")

# DART 보고서 타입 그룹 정의
REPORT_GROUPS = {
    'daily': {  # 매일 수집
        'F001': '회사합병결정',
        'F002': '영업양수도결정',
        'F006': '유상증자결정',
        'F009': '주식분할결정',
        'F014': '전환사채발행결정',
        'G001': '대표이사변경',
        'G002': '임원변경',
        'G003': '감사변경',
        'A004': '주요사항보고서'
    },
    'weekly': {  # 주간 수집
        'A005': '감사보고서'
    },
    'monthly': {  # 월간 수집
        'A001': '사업보고서',
        'A002': '반기보고서',
        'A003': '분기보고서'
    }
}

@pytest.mark.integration
class TestDartCollection:
    @pytest.fixture(autouse=True)
    def setup(self, pg_test_config, temp_vector_store_path, dart_api_key):
        """테스트 환경 설정"""
        self.db_config = pg_test_config
        self.vector_store_path = temp_vector_store_path
        self.client = DartClient(dart_api_key)
        self.pipeline = RAGPipeline(str(self.vector_store_path))
        
        # 테스트 기업 설정
        self.test_corps = [
            ("00126380", "삼성전자"),  # 대표 기업 하나만 테스트
        ]
        
        # 테스트 DB 초기화
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                # 기존 테이블 삭제
                cur.execute("DROP TABLE IF EXISTS dart_reports")
                
                # 테이블 생성
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS dart_reports (
                        id SERIAL PRIMARY KEY,
                        corp_code VARCHAR(8) NOT NULL,
                        corp_name VARCHAR(100) NOT NULL,
                        receipt_no VARCHAR(14) NOT NULL UNIQUE,
                        report_type VARCHAR(100) NOT NULL,
                        title VARCHAR(300) NOT NULL,
                        content TEXT NOT NULL,
                        disclosure_date DATE NOT NULL,
                        meta_data JSONB
                    )
                """)
                
                # 인덱스 생성
                cur.execute("CREATE INDEX IF NOT EXISTS idx_dart_reports_corp_code ON dart_reports(corp_code)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_dart_reports_receipt_no ON dart_reports(receipt_no)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_dart_reports_disclosure_date ON dart_reports(disclosure_date)")
                
                conn.commit()
        
        yield
        
        # 테스트 후 정리
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS dart_reports")
                conn.commit()

    @pytest.mark.asyncio
    async def test_corp_codes(self):
        """기업 목록 조회 테스트"""
        corps = await self.client.get_corp_codes()
        assert len(corps) > 0
        assert isinstance(corps[0], dict)
        assert 'corp_code' in corps[0]
        assert 'corp_name' in corps[0]

    @pytest.mark.asyncio
    async def test_disclosure_collection(self):
        """공시 수집 테스트"""
        corp_code, corp_name = self.test_corps[0]
        
        # 일간 공시 수집 테스트
        documents = await self._collect_disclosures(corp_code, corp_name, 'daily', 1)
        assert isinstance(documents, list)
        
        if documents:
            # 문서 처리 테스트
            success = self.process_documents(documents)
            assert success is True
            
            # DB에 저장되었는지 확인
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("SELECT * FROM dart_reports WHERE corp_code = %s", (corp_code,))
                    saved_docs = cur.fetchall()
                    assert len(saved_docs) > 0
                    assert saved_docs[0]['corp_code'] == corp_code

    async def _collect_disclosures(
        self,
        corp_code: str,
        corp_name: str,
        report_group: str,
        days: int
    ) -> Optional[List[Dict]]:
        """공시 수집 헬퍼 함수"""
        try:
            # 수집 기간 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 공시 목록 조회
            disclosures = await self.client.get_disclosure_list(
                corp_code=corp_code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )
            
            # 해당 그룹의 보고서만 필터링
            target_report_types = REPORT_GROUPS.get(report_group, {})
            filtered_disclosures = [
                disc for disc in disclosures
                if disc.get('report_tp') in target_report_types
            ]
            
            # 공시 상세 내용 수집 (최대 10개만 테스트)
            test_disclosures = filtered_disclosures[:10]
            
            results = []
            for disc in test_disclosures:
                try:
                    document = await self.client.get_document(disc['rcept_no'])
                    if document:
                        # 메타데이터 보강
                        document['report_type'] = target_report_types.get(
                            disc.get('report_tp'), '기타'
                        )
                        document['collection_group'] = report_group
                        results.append(document)
                except Exception:
                    continue
            
            return results
            
        except Exception:
            return None

    def process_documents(self, documents: List[Dict]) -> bool:
        """문서 처리 및 저장 테스트"""
        if not documents:
            return False
        
        try:
            # DartCollector 초기화
            collector = DartCollector(
                db_config=self.db_config,
                rag_pipeline=self.pipeline,
                vector_store_enabled=True
            )
            
            # 각 문서 처리
            for doc in documents:
                # metadata 필드 처리 개선
                if 'metadata' in doc:
                    doc['meta_data'] = doc.pop('metadata')
                elif 'meta_data' in doc:
                    pass  # 이미 올바른 형식
                else:
                    doc['meta_data'] = {}  # 기본값 설정
                
                success = collector.process_document(doc)
                if not success:
                    return False
            return True
        except Exception as e:
            print(f"문서 처리 중 오류 발생: {str(e)}")
            return False

async def main():
    """테스트 실행"""
    # 증분 수집 테스트
    print("\n=== 증분 수집 테스트 시작 ===")
    incremental_tester = TestDartCollection()
    await incremental_tester.test_disclosure_collection()
    
    # 초기 수집 테스트
    print("\n=== 초기 수집 테스트 시작 ===")
    initial_tester = TestDartCollection()
    await initial_tester.test_disclosure_collection()

if __name__ == "__main__":
    asyncio.run(main()) 
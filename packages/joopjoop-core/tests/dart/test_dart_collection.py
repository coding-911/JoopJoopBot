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
from joopjoop.dart.utils import parse_date

# 프로젝트 루트 디렉토리 찾기
def find_project_root() -> Path:
    """프로젝트 루트 디렉토리 찾기"""
    current = Path(__file__).resolve().parent
    while current.name != "JoopJoopBot" and current.parent != current:
        current = current.parent
    return current

@pytest.fixture(scope="session")
def project_root():
    """프로젝트 루트 경로"""
    return find_project_root()

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

class TestDartCollector:
    @pytest.fixture(autouse=True)
    def setup(self, temp_db_connection, temp_vector_store_path, dart_api_key):
        """테스트 환경 설정"""
        self.db_conn = temp_db_connection
        self.vector_store_path = temp_vector_store_path
        self.client = DartClient(dart_api_key)
        
        # RAG 파이프라인 초기화
        self.rag_pipeline = RAGPipeline(self.vector_store_path)
        
        # DartCollector 초기화
        self.collector = DartCollector(
            db_connection=self.db_conn,
            rag_pipeline=self.rag_pipeline,
            vector_store_enabled=True
        )
    
    def test_process_document(self):
        """문서 처리 테스트"""
        # 테스트용 문서 데이터
        test_date = datetime.now()
        test_doc = {
            'corp_code': 'TEST001',
            'corp_name': '테스트기업',
            'receipt_no': 'TEST_RCPT_001',
            'report_type': '주요사항보고서',
            'title': '테스트 공시',
            'content': '이 문서는 테스트를 위한 공시 문서입니다.',
            'disclosure_date': test_date.strftime("%Y-%m-%d"),  # DB 저장용 포맷
            'dcm_no': 'TEST_DCM_001',
            'url': 'http://test.com',
            'file_name': 'test.pdf',
            'page_count': 1
        }
        
        # 문서 처리
        success = self.collector.process_document(test_doc)
        assert success is True
        
        # DB에 저장되었는지 확인
        with self.db_conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM dart_reports 
                WHERE receipt_no = %s
            """, ('TEST_RCPT_001',))
            result = cur.fetchone()
            
            assert result is not None
            assert result['corp_code'] == 'TEST001'
            assert result['corp_name'] == '테스트기업'
            assert result['report_type'] == '주요사항보고서'
            assert result['title'] == '테스트 공시'
    
    def test_process_duplicate_document(self):
        """중복 문서 처리 테스트"""
        # 테스트용 문서 데이터
        test_date = datetime.now()
        test_doc = {
            'corp_code': 'TEST002',
            'corp_name': '테스트기업2',
            'receipt_no': 'TEST_RCPT_002',
            'report_type': '주요사항보고서',
            'title': '테스트 공시2',
            'content': '이 문서는 테스트를 위한 공시 문서입니다.',
            'disclosure_date': test_date.strftime("%Y-%m-%d"),  # DB 저장용 포맷
            'dcm_no': 'TEST_DCM_001',
            'url': 'http://test.com',
            'file_name': 'test.pdf',
            'page_count': 1
        }
        
        # 첫 번째 처리
        success1 = self.collector.process_document(test_doc)
        assert success1 is True
        
        # 두 번째 처리 (중복)
        success2 = self.collector.process_document(test_doc)
        assert success2 is False
        
        # DB에 하나만 저장되었는지 확인
        with self.db_conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM dart_reports 
                WHERE receipt_no = %s
            """, ('TEST_RCPT_002',))
            count = cur.fetchone()[0]
            assert count == 1
    
    @pytest.mark.asyncio
    async def test_collect_recent_reports(self):
        """최근 보고서 수집 테스트"""
        # 삼성전자 최근 공시 수집
        corp_code = "00126380"  # 삼성전자
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 공시 목록 조회
        disclosures = await self.client.get_disclosure_list(
            corp_code=corp_code,
            start_date=start_date.strftime("%Y%m%d"),  # API 요청용 포맷
            end_date=end_date.strftime("%Y%m%d")      # API 요청용 포맷
        )
        
        assert len(disclosures) > 0
        
        # 첫 번째 공시 상세 조회 및 처리
        first_disc = disclosures[0]
        document = await self.client.get_document(first_disc['rcept_no'])
        
        assert document is not None
        
        # 문서 형식 변환
        rcept_dt = datetime.strptime(first_disc.get('rcept_dt', end_date.strftime("%Y%m%d")), '%Y%m%d')
        processed_document = {
            'corp_code': corp_code,
            'corp_name': document['corp_name'],
            'receipt_no': document['receipt_no'],
            'report_type': first_disc.get('report_nm', '기타'),
            'title': document['title'],
            'content': document['content'],
            'disclosure_date': rcept_dt.strftime("%Y-%m-%d"),  # DB 저장용 포맷
            'dcm_no': document.get('dcm_no', ''),
            'url': f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={document['receipt_no']}",
            'file_name': f"{document['receipt_no']}.pdf",
            'page_count': 1
        }
        
        # 문서 처리
        success = self.collector.process_document(processed_document)
        assert success is True
        
        # DB에 저장되었는지 확인
        with self.db_conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM dart_reports 
                WHERE receipt_no = %s
            """, (first_disc['rcept_no'],))
            result = cur.fetchone()
            
            assert result is not None
            assert result['corp_code'] == corp_code
            assert result['receipt_no'] == first_disc['rcept_no']

@pytest.mark.integration
class TestDartCollection:
    @pytest.fixture(autouse=True)
    def setup(self, temp_db_config, temp_vector_store_path, dart_api_key):
        """테스트 환경 설정"""
        self.db_config = temp_db_config
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
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import pytest
from joopjoop.rag import RAGPipeline

# 프로젝트 루트 디렉토리 찾기
def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current.name != "JoopJoopBot" and current.parent != current:
        current = current.parent
    return current

# 환경변수 로드
project_root = find_project_root()
load_dotenv(project_root / ".env")

@pytest.mark.integration
class TestRAGPipeline:
    @pytest.fixture(autouse=True)
    def setup(self, temp_vector_store_path):
        """테스트 환경 설정"""
        self.vector_store_path = temp_vector_store_path
        self.pipeline = RAGPipeline(str(self.vector_store_path))
        
        yield
    
    def teardown_method(self):
        """테스트 종료 후 정리"""
        try:
            shutil.rmtree(self.vector_store_path)
            print(f"\n임시 벡터 DB 삭제 완료: {self.vector_store_path}")
        except Exception as e:
            print(f"\n임시 벡터 DB 삭제 실패: {str(e)}")
    
    def test_document_processing(self):
        """문서 처리 테스트"""
        # 테스트용 문서 데이터
        test_document = {
            'title': '테스트 공시',
            'content': '이 문서는 테스트를 위한 공시 문서입니다.',
            'report_type': '주요사항보고서',
            'collection_group': 'daily',
            'rcept_no': 'TEST001',
            'corp_code': '00126380',
            'corp_name': '삼성전자'
        }
        
        # 문서 처리
        self.pipeline.process_document(test_document)
        
        # 벡터 DB에 저장되었는지 확인
        results = self.pipeline.search(
            query="테스트 공시",
            top_k=1
        )
        
        assert len(results) == 1
        assert results[0]['title'] == '테스트 공시'
        assert results[0]['corp_name'] == '삼성전자'
    
    def test_search_functionality(self):
        """검색 기능 테스트"""
        # 여러 테스트 문서 추가
        test_documents = [
            {
                'title': '유상증자 결정',
                'content': '당사는 신규 사업 투자를 위해 유상증자를 결정하였습니다.',
                'report_type': '유상증자결정',
                'collection_group': 'daily',
                'rcept_no': 'TEST001',
                'corp_code': '00126380',
                'corp_name': '삼성전자'
            },
            {
                'title': '대표이사 변경',
                'content': '당사는 이사회를 통해 신임 대표이사 선임을 결정하였습니다.',
                'report_type': '대표이사변경',
                'collection_group': 'daily',
                'rcept_no': 'TEST002',
                'corp_code': '00126380',
                'corp_name': '삼성전자'
            }
        ]
        
        # 문서 처리
        for doc in test_documents:
            self.pipeline.process_document(doc)
        
        # 검색 테스트
        results = self.pipeline.search(
            query="유상증자 결정",
            top_k=2
        )
        
        assert len(results) == 2
        assert results[0]['title'] == '유상증자 결정'  # 가장 관련성 높은 문서
        
        # 기업 필터링 테스트
        filtered_results = self.pipeline.search(
            query="대표이사",
            corp_code="00126380",
            top_k=1
        )
        
        assert len(filtered_results) == 1
        assert filtered_results[0]['title'] == '대표이사 변경'
        assert filtered_results[0]['corp_code'] == '00126380'
    
    def test_metadata_filtering(self):
        """메타데이터 필터링 테스트"""
        # 다양한 메타데이터를 가진 테스트 문서 추가
        test_documents = [
            {
                'title': '사업보고서',
                'content': '2023년 사업보고서입니다.',
                'report_type': '사업보고서',
                'collection_group': 'monthly',
                'rcept_no': 'TEST001',
                'corp_code': '00126380',
                'corp_name': '삼성전자'
            },
            {
                'title': '주요사항보고서',
                'content': '신규 사업 진출 관련 공시입니다.',
                'report_type': '주요사항보고서',
                'collection_group': 'daily',
                'rcept_no': 'TEST002',
                'corp_code': '00164779',
                'corp_name': '현대자동차'
            }
        ]
        
        # 문서 처리
        for doc in test_documents:
            self.pipeline.process_document(doc)
        
        # 보고서 타입 필터링 테스트
        results = self.pipeline.search(
            query="사업",
            report_type="사업보고서",
            top_k=1
        )
        
        assert len(results) == 1
        assert results[0]['report_type'] == '사업보고서'
        
        # 수집 그룹 필터링 테스트
        results = self.pipeline.search(
            query="신규 사업",
            collection_group="daily",
            top_k=1
        )
        
        assert len(results) == 1
        assert results[0]['collection_group'] == 'daily' 
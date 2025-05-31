import asyncio
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from joopjoop.dart import DartClient
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

class DartCollectionTester:
    def __init__(self, test_mode: str = 'incremental'):
        """
        Args:
            test_mode: 테스트 모드 ('incremental' 또는 'initial')
                - incremental: 증분 수집 테스트 (일/주/월간)
                - initial: 초기 수집 테스트 (1년치)
        """
        self.api_key = os.getenv("DART_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DART_API_KEY 환경변수가 설정되지 않았습니다.\n"
                f"프로젝트 루트({project_root})의 .env 파일을 확인해주세요."
            )
        
        self.test_mode = test_mode
        
        # 테스트용 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp(prefix=f"dart_test_{test_mode}_")
        self.vector_store_path = Path(self.temp_dir) / "vector_store"
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n임시 벡터 DB 경로: {self.vector_store_path}")
        
        self.client = DartClient(self.api_key)
        self.pipeline = RAGPipeline(str(self.vector_store_path))
        
        # 테스트 기업 설정
        if test_mode == 'initial':
            # 초기 수집은 기업 수를 제한
            self.test_corps = [
                ("00126380", "삼성전자"),  # 대표 기업 하나만 테스트
            ]
        else:
            # 증분 수집은 여러 기업 테스트
            self.test_corps = [
                ("00126380", "삼성전자"),
                ("00164779", "현대자동차"),
                ("00164742", "SK하이닉스"),
                ("00258801", "카카오")
            ]

    def cleanup(self):
        """테스트 종료 후 임시 디렉토리 삭제"""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"\n임시 벡터 DB 삭제 완료: {self.temp_dir}")
        except Exception as e:
            print(f"\n임시 벡터 DB 삭제 실패: {str(e)}")

    async def test_corp_codes(self) -> bool:
        """기업 목록 조회 테스트"""
        print("\n=== 기업 목록 조회 테스트 ===")
        try:
            corps = await self.client.get_corp_codes()
            print(f"- 전체 기업 수: {len(corps)}")
            if corps:
                print(f"- 샘플 기업: {corps[0]}")
            return True
        except Exception as e:
            print(f"Error: {str(e)}")
            return False

    async def test_disclosure_collection(
        self,
        corp_code: str,
        corp_name: str,
        report_group: str,
        days: int
    ) -> Optional[List[Dict]]:
        """특정 기업의 공시 수집 테스트"""
        print(f"\n=== {corp_name} ({report_group}) 공시 수집 테스트 ===")
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
            if not target_report_types and report_group == 'all':
                # 초기 수집의 경우 모든 보고서 타입 통합
                target_report_types = {
                    k: v for group in REPORT_GROUPS.values() 
                    for k, v in group.items()
                }
            
            filtered_disclosures = [
                disc for disc in disclosures
                if disc.get('report_tp') in target_report_types
            ]
            
            print(f"- 전체 공시 수: {len(disclosures)}")
            print(f"- 필터링된 공시 수: {len(filtered_disclosures)}")
            
            # 공시 상세 내용 수집 (최대 10개만 테스트)
            test_disclosures = filtered_disclosures[:10]
            if len(filtered_disclosures) > 10:
                print(f"- 테스트를 위해 처음 10개의 공시만 처리합니다 (전체: {len(filtered_disclosures)}개)")
            
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
                        print(f"- 문서 수집 성공: {disc.get('report_nm')} ({disc.get('rcept_no')})")
                except Exception as e:
                    print(f"- 문서 수집 실패: {disc.get('rcept_no')} - {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def process_documents(self, documents: List[Dict]) -> bool:
        """문서 처리 및 벡터 DB 저장 테스트"""
        if not documents:
            return False
        
        try:
            for doc in documents:
                self.pipeline.process_document(doc)
                print(f"- 문서 처리 성공: {doc.get('title')} ({doc.get('report_type')})")
            return True
        except Exception as e:
            print(f"Error: {str(e)}")
            return False

    async def run_incremental_tests(self):
        """증분 수집 테스트 실행 (일/주/월간)"""
        collection_configs = [
            ('daily', 1),    # 일간 수집 (1일)
            ('weekly', 7),   # 주간 수집 (7일)
            ('monthly', 30)  # 월간 수집 (30일)
        ]
        
        for corp_code, corp_name in self.test_corps:
            for report_group, days in collection_configs:
                documents = await self.test_disclosure_collection(
                    corp_code, corp_name, report_group, days
                )
                if documents:
                    self.process_documents(documents)

    async def run_initial_tests(self):
        """초기 수집 테스트 실행 (1년치)"""
        for corp_code, corp_name in self.test_corps:
            documents = await self.test_disclosure_collection(
                corp_code, corp_name, 'all', 365
            )
            if documents:
                self.process_documents(documents)

    async def run_all_tests(self):
        """모든 테스트 실행"""
        try:
            # 1. 기업 목록 조회 테스트
            if not await self.test_corp_codes():
                return
            
            # 2. 테스트 모드에 따라 수집 테스트 실행
            if self.test_mode == 'incremental':
                await self.run_incremental_tests()
            else:
                await self.run_initial_tests()
                
        finally:
            self.cleanup()

async def main():
    """테스트 실행"""
    # 증분 수집 테스트
    print("\n=== 증분 수집 테스트 시작 ===")
    incremental_tester = DartCollectionTester('incremental')
    await incremental_tester.run_all_tests()
    
    # 초기 수집 테스트
    print("\n=== 초기 수집 테스트 시작 ===")
    initial_tester = DartCollectionTester('initial')
    await initial_tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
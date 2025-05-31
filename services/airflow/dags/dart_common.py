from datetime import datetime, timedelta
import os
import asyncio
from typing import List, Dict
import logging

from joopjoop.dart import DartClient
from joopjoop.dart.corp_manager import CorpManager
from joopjoop.rag import RAGPipeline

# 환경변수
DART_API_KEY = os.getenv("DART_API_KEY")
VECTOR_STORE_PATH = os.getenv("VECTOR_DB_PATH", "/opt/airflow/vector_store")
CORPS_DB_PATH = os.getenv("CORPS_DB_PATH", "/opt/airflow/data/corps.db")
ALERT_EMAIL = os.getenv("AIRFLOW_ALERT_EMAIL")

# 보고서 타입 그룹
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

# 수집 기간 설정
COLLECTION_PERIODS = {
    'daily': 1,      # 1일
    'weekly': 7,     # 7일
    'monthly': 30    # 30일
}

logger = logging.getLogger(__name__)

# Airflow DAG 기본 설정
default_args = {
    'owner': 'joopjoop',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ALERT_EMAIL,
    'email_on_failure': bool(ALERT_EMAIL),
    'email_on_retry': bool(ALERT_EMAIL),
    'retries': int(os.getenv("AIRFLOW_TASK_RETRIES", "1")),
    'retry_delay': timedelta(minutes=int(os.getenv("AIRFLOW_RETRY_DELAY_MINUTES", "5"))),
}

async def update_corps() -> None:
    """기업 목록 업데이트"""
    client = DartClient(DART_API_KEY)
    corp_manager = CorpManager(CORPS_DB_PATH)
    
    try:
        corps = await client.get_corp_codes()
        corp_manager.upsert_corps(corps)
        logger.info(f"기업 목록 업데이트 완료: {len(corps)}개 기업")
    except Exception as e:
        logger.error(f"기업 목록 업데이트 실패: {str(e)}")
        raise

def get_corps(only_listed: bool = False) -> List[Dict]:
    """기업 목록 조회"""
    corp_manager = CorpManager(CORPS_DB_PATH)
    corps = corp_manager.get_all_corps(only_listed=only_listed)
    logger.info(f"기업 목록 조회 완료: {len(corps)}개 기업")
    return corps

async def fetch_disclosures(corp: Dict, report_group: str) -> List[Dict]:
    """공시 목록 및 상세 조회"""
    client = DartClient(DART_API_KEY)
    corp_manager = CorpManager(CORPS_DB_PATH)
    
    try:
        # 보고서 그룹에 따른 수집 기간 설정
        days = COLLECTION_PERIODS[report_group]
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        end_date = datetime.now().strftime('%Y%m%d')
        
        # 공시 목록 조회
        disclosures = await client.get_disclosure_list(
            corp_code=corp['corp_code'],
            start_date=start_date,
            end_date=end_date
        )
        
        # 해당 그룹의 보고서만 필터링
        target_report_types = REPORT_GROUPS[report_group]
        filtered_disclosures = [
            disc for disc in disclosures
            if disc.get('report_tp') in target_report_types
        ]
        
        # 각 공시의 상세 내용 조회
        results = []
        for disc in filtered_disclosures:
            try:
                document = await client.get_document(disc['rcept_no'])
                if document:
                    # 메타데이터 보강
                    document['report_type'] = target_report_types.get(
                        disc.get('report_tp'), '기타'
                    )
                    document['collection_group'] = report_group
                    document['corp_name'] = corp['corp_name']
                    document['corp_code'] = corp['corp_code']
                    document['stock_code'] = corp.get('stock_code')
                    results.append(document)
                    logger.info(f"문서 수집 성공: {disc.get('report_nm')} ({disc.get('rcept_no')})")
            except Exception as e:
                logger.error(f"문서 수집 실패: {disc.get('rcept_no')} - {str(e)}")
                continue
        
        # 수집 완료 시간 업데이트
        if results:
            corp_manager.update_collection_timestamp(corp['corp_code'])
        
        return results
    
    except Exception as e:
        logger.error(f"기업 공시 목록 조회 실패 (기업: {corp['corp_name']}): {str(e)}")
        return []

def process_documents(documents: List[Dict]) -> None:
    """문서 처리 및 벡터 DB 저장"""
    pipeline = RAGPipeline(VECTOR_STORE_PATH)
    for doc in documents:
        try:
            pipeline.process_document(doc)
            logger.info(f"문서 처리 성공: {doc.get('title')} ({doc.get('report_type')})")
        except Exception as e:
            logger.error(f"문서 처리 실패: {doc.get('title')} - {str(e)}")

def run_update_corps():
    """기업 목록 업데이트 실행"""
    asyncio.run(update_corps())

def run_fetch_disclosures(report_group: str, only_listed: bool = False):
    """공시 조회 및 처리 실행"""
    corps = get_corps(only_listed=only_listed)
    for corp in corps:
        try:
            documents = asyncio.run(fetch_disclosures(corp, report_group))
            if documents:
                process_documents(documents)
                logger.info(f"기업 데이터 수집 완료: {corp['corp_name']} (그룹: {report_group})")
        except Exception as e:
            logger.error(f"기업 데이터 수집 실패: {corp['corp_name']} - {str(e)}") 
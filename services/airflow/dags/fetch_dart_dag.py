from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os
import asyncio
from typing import List, Dict
import logging

from joopjoop.dart import DartClient
from joopjoop.rag import RAGPipeline

# 환경변수
DART_API_KEY = os.getenv("DART_API_KEY")
VECTOR_STORE_PATH = os.getenv("VECTOR_DB_PATH", "/opt/airflow/vector_store")
ALERT_EMAIL = os.getenv("AIRFLOW_ALERT_EMAIL")

# 중요 보고서 타입
IMPORTANT_REPORT_TYPES = {
    # 사업보고서 관련
    'A001': '사업보고서',
    'A002': '반기보고서',
    'A003': '분기보고서',
    
    # 주요 공시
    'A004': '주요사항보고서',
    'A005': '감사보고서',
    'F001': '회사합병결정',
    'F002': '영업양수도결정',
    'F006': '유상증자결정',
    'F009': '주식분할결정',
    'F014': '전환사채발행결정',
    
    # 지배구조 관련
    'G001': '대표이사변경',
    'G002': '임원변경',
    'G003': '감사변경'
}

logger = logging.getLogger(__name__)

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

async def fetch_corps() -> List[Dict]:
    """기업 목록 조회"""
    client = DartClient(DART_API_KEY)
    return await client.get_corp_codes()

async def fetch_disclosures(corp_code: str) -> List[Dict]:
    """공시 목록 및 상세 조회"""
    client = DartClient(DART_API_KEY)
    
    try:
        # 최근 7일간의 공시 목록 조회
        disclosures = await client.get_disclosure_list(
            corp_code=corp_code,
            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d')
        )
        
        # 중요 공시만 필터링
        important_disclosures = [
            disc for disc in disclosures
            if disc.get('report_tp') in IMPORTANT_REPORT_TYPES
        ]
        
        # 각 공시의 상세 내용 조회
        results = []
        for disc in important_disclosures:
            try:
                document = await client.get_document(disc['rcept_no'])
                if document:
                    # 메타데이터 보강
                    document['report_type'] = IMPORTANT_REPORT_TYPES.get(
                        disc.get('report_tp'), '기타'
                    )
                    results.append(document)
                    logger.info(f"문서 수집 성공: {disc.get('report_nm')} ({disc.get('rcept_no')})")
            except Exception as e:
                logger.error(f"문서 수집 실패: {disc.get('rcept_no')} - {str(e)}")
                continue
        
        return results
    
    except Exception as e:
        logger.error(f"기업 공시 목록 조회 실패 (기업코드: {corp_code}): {str(e)}")
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

def run_fetch_corps():
    """기업 목록 조회 실행"""
    corps = asyncio.run(fetch_corps())
    return [corp['corp_code'] for corp in corps]

def run_fetch_disclosures(corp_codes: List[str]):
    """공시 조회 및 처리 실행"""
    for corp_code in corp_codes:
        try:
            documents = asyncio.run(fetch_disclosures(corp_code))
            if documents:
                process_documents(documents)
                logger.info(f"기업 데이터 수집 완료: {corp_code}")
        except Exception as e:
            logger.error(f"기업 데이터 수집 실패: {corp_code} - {str(e)}")

with DAG(
    'fetch_dart_data',
    default_args=default_args,
    description='DART 데이터 일일 수집 및 벡터 DB 저장',
    schedule_interval='0 0 * * *',  # 매일 자정
    catchup=False
) as dag:

    fetch_corps_task = PythonOperator(
        task_id='fetch_corps',
        python_callable=run_fetch_corps,
    )

    fetch_disclosures_task = PythonOperator(
        task_id='fetch_disclosures',
        python_callable=run_fetch_disclosures,
        op_kwargs={'corp_codes': "{{ task_instance.xcom_pull(task_ids='fetch_corps') }}"},
    )

    fetch_corps_task >> fetch_disclosures_task 
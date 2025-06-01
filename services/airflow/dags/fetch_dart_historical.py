from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import asyncio
from typing import List, Dict
import logging
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta

from dart_common import (
    default_args,
    REPORT_GROUPS,
    DartClient,
    DartCollector,
    RAGPipeline,
    DART_API_KEY,
    VECTOR_STORE_PATH,
    DB_CONFIG
)

logger = logging.getLogger(__name__)

# 모든 중요 보고서 타입 통합
ALL_REPORT_TYPES = {}
for group_types in REPORT_GROUPS.values():
    ALL_REPORT_TYPES.update(group_types)

async def fetch_historical_disclosures(
    corp_code: str,
    start_date: str = None,
    end_date: str = None
) -> List[Dict]:
    """과거 공시 목록 및 상세 조회"""
    client = DartClient(DART_API_KEY)
    
    try:
        # 공시 목록 조회
        disclosures = await client.get_disclosure_list(
            corp_code=corp_code,
            start_date=start_date,
            end_date=end_date
        )
        
        # 중요 보고서만 필터링
        filtered_disclosures = [
            disc for disc in disclosures
            if disc.get('report_tp') in ALL_REPORT_TYPES
        ]
        
        # 각 공시의 상세 내용 조회
        results = []
        for disc in filtered_disclosures:
            try:
                document = await client.get_document(disc['rcept_no'])
                if document:
                    # 메타데이터 보강
                    document['report_type'] = ALL_REPORT_TYPES.get(
                        disc.get('report_tp'), '기타'
                    )
                    document['disclosure_date'] = disc.get('rcept_dt')
                    results.append(document)
                    logger.info(f"문서 수집 성공: {disc.get('report_nm')} ({disc.get('rcept_no')})")
            except Exception as e:
                logger.error(f"문서 수집 실패: {disc.get('rcept_no')} - {str(e)}")
                continue
        
        return results
    
    except Exception as e:
        logger.error(f"기업 공시 목록 조회 실패 (기업코드: {corp_code}): {str(e)}")
        return []

def process_historical_documents(documents: List[Dict]) -> None:
    """과거 문서 처리 및 저장"""
    if not documents:
        return

    # PostgreSQL 연결
    with psycopg2.connect(**DB_CONFIG, cursor_factory=DictCursor) as conn:
        with conn.cursor() as cur:
            # RAG 파이프라인 초기화
            rag_pipeline = RAGPipeline(VECTOR_STORE_PATH)
            
            # DartCollector 초기화
            collector = DartCollector(
                db_connection=conn,
                rag_pipeline=rag_pipeline,
                vector_store_enabled=True
            )
            
            # 각 문서 처리
            for doc in documents:
                try:
                    success = collector.process_document(doc)
                    if success:
                        logger.info(f"문서 처리 성공: {doc.get('title')} ({doc.get('report_type')})")
                    else:
                        logger.warning(f"문서 처리 실패 또는 중복: {doc.get('title')}")
                except Exception as e:
                    logger.error(f"문서 처리 중 오류 발생: {str(e)}")
                    continue

def run_fetch_historical_disclosures(corp_codes: List[str], **context):
    """과거 공시 수집 실행"""
    # 수집 기간 설정 (1년)
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    # 진행 상황 추적을 위한 변수
    processed_corps = Variable.get("processed_corps", default_var=[], deserialize_json=True)
    failed_corps = Variable.get("failed_corps", default_var=[], deserialize_json=True)
    
    for corp_code in corp_codes:
        if corp_code in processed_corps:
            logger.info(f"이미 처리된 기업 건너뛰기: {corp_code}")
            continue
            
        try:
            documents = asyncio.run(fetch_historical_disclosures(
                corp_code=corp_code,
                start_date=start_date,
                end_date=end_date
            ))
            
            if documents:
                process_historical_documents(documents)
                processed_corps.append(corp_code)
                Variable.set("processed_corps", processed_corps, serialize_json=True)
                logger.info(f"기업 과거 데이터 수집 완료: {corp_code}")
            
        except Exception as e:
            logger.error(f"기업 과거 데이터 수집 실패: {corp_code} - {str(e)}")
            failed_corps.append(corp_code)
            Variable.set("failed_corps", failed_corps, serialize_json=True)

# DAG 정의
with DAG(
    'fetch_dart_historical',
    default_args=default_args,
    description='과거 DART 공시 데이터 수집',
    schedule_interval=None,  # 수동 실행
    tags=['dart', 'historical']
) as dag:
    
    fetch_historical = PythonOperator(
        task_id='fetch_historical_disclosures',
        python_callable=run_fetch_historical_disclosures,
        op_kwargs={'corp_codes': []},  # 실행 시 기업 코드 목록 전달
    ) 
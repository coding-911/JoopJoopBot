from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import asyncio
from typing import List, Dict
import logging

from dart_common import (
    default_args,
    REPORT_GROUPS,
    DartClient,
    RAGPipeline,
    DART_API_KEY,
    VECTOR_STORE_PATH,
    process_documents,
    run_fetch_corps
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
        
        # 중요 공시만 필터링
        important_disclosures = [
            disc for disc in disclosures
            if disc.get('report_tp') in ALL_REPORT_TYPES
        ]
        
        # 각 공시의 상세 내용 조회
        results = []
        for disc in important_disclosures:
            try:
                document = await client.get_document(disc['rcept_no'])
                if document:
                    # 메타데이터 보강
                    document['report_type'] = ALL_REPORT_TYPES.get(
                        disc.get('report_tp'), '기타'
                    )
                    document['collection_group'] = 'historical'
                    results.append(document)
                    logger.info(f"문서 수집 성공: {disc.get('report_nm')} ({disc.get('rcept_no')})")
            except Exception as e:
                logger.error(f"문서 수집 실패: {disc.get('rcept_no')} - {str(e)}")
                continue
        
        return results
    
    except Exception as e:
        logger.error(f"기업 공시 목록 조회 실패 (기업코드: {corp_code}): {str(e)}")
        return []

def run_fetch_historical_disclosures(corp_codes: List[str], **context):
    """과거 공시 조회 및 처리 실행"""
    # 이미 수집된 기업 목록 가져오기
    collected_corps = Variable.get("collected_corps", deserialize_json=True, default=[])
    
    for corp_code in corp_codes:
        # 이미 수집된 기업은 스킵
        if corp_code in collected_corps:
            logger.info(f"이미 수집된 기업 스킵: {corp_code}")
            continue
            
        try:
            # 과거 1년치 공시 수집
            documents = asyncio.run(fetch_historical_disclosures(corp_code))
            if documents:
                process_documents(documents)
                # 수집 완료된 기업 저장
                collected_corps.append(corp_code)
                Variable.set("collected_corps", collected_corps, serialize_json=True)
                logger.info(f"기업 데이터 수집 완료: {corp_code}")
        except Exception as e:
            logger.error(f"기업 데이터 수집 실패: {corp_code} - {str(e)}")

with DAG(
    'fetch_dart_historical',
    default_args=default_args,
    description='DART 과거 데이터 수집 및 벡터 DB 저장',
    schedule_interval=None,  # 수동 실행
    catchup=False
) as dag:

    fetch_corps_task = PythonOperator(
        task_id='fetch_corps',
        python_callable=run_fetch_corps,
    )

    fetch_historical_task = PythonOperator(
        task_id='fetch_historical_disclosures',
        python_callable=run_fetch_historical_disclosures,
        op_kwargs={'corp_codes': "{{ task_instance.xcom_pull(task_ids='fetch_corps') }}"},
    )

    fetch_corps_task >> fetch_historical_task 
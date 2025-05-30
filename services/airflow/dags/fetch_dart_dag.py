from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os
import asyncio
from typing import List, Dict

from joopjoop.dart import DartClient
from joopjoop.rag import RAGPipeline

# 환경변수
DART_API_KEY = os.getenv("DART_API_KEY")
VECTOR_STORE_PATH = os.getenv("VECTOR_DB_PATH", "/opt/airflow/vector_store")
ALERT_EMAIL = os.getenv("AIRFLOW_ALERT_EMAIL")

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
    
    # 최근 7일간의 공시 목록 조회
    disclosures = await client.get_disclosure_list(
        corp_code=corp_code,
        start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
        end_date=datetime.now().strftime('%Y%m%d')
    )
    
    # 각 공시의 상세 내용 조회
    results = []
    for disc in disclosures:
        document = await client.get_document(disc['rcept_no'])
        if document:
            results.append(document)
    
    return results

def process_documents(documents: List[Dict]) -> None:
    """문서 처리 및 벡터 DB 저장"""
    pipeline = RAGPipeline(VECTOR_STORE_PATH)
    for doc in documents:
        pipeline.process_document(doc)

def run_fetch_corps():
    """기업 목록 조회 실행"""
    corps = asyncio.run(fetch_corps())
    return [corp['corp_code'] for corp in corps]

def run_fetch_disclosures(corp_codes: List[str]):
    """공시 조회 및 처리 실행"""
    for corp_code in corp_codes:
        documents = asyncio.run(fetch_disclosures(corp_code))
        if documents:
            process_documents(documents)

with DAG(
    'fetch_dart_data',
    default_args=default_args,
    description='DART 데이터 수집 및 벡터 DB 저장',
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
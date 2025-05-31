from airflow import DAG
from airflow.operators.python import PythonOperator

from dart_common import (
    default_args,
    run_update_corps,
    run_fetch_disclosures
)

with DAG(
    'fetch_dart_monthly',
    default_args=default_args,
    description='DART 데이터 월간 수집 (정기보고서)',
    schedule_interval='0 0 1 * *',  # 매월 1일
    catchup=False
) as dag:
    # 1. 전체 기업 목록 업데이트
    update_corps_task = PythonOperator(
        task_id='update_corps',
        python_callable=run_update_corps,
    )
    
    # 2. 전체 기업의 월간 보고서 수집
    fetch_disclosures_task = PythonOperator(
        task_id='fetch_disclosures',
        python_callable=run_fetch_disclosures,
        op_kwargs={
            'report_group': 'monthly',
            'only_listed': False  # 전체 기업 대상
        },
    )
    
    update_corps_task >> fetch_disclosures_task 
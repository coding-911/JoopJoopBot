from airflow import DAG
from airflow.operators.python import PythonOperator

from dart_common import (
    default_args,
    run_fetch_disclosures
)

with DAG(
    'fetch_dart_daily',
    default_args=default_args,
    description='DART 데이터 일간 수집 (주요 공시)',
    schedule_interval='0 18 * * 1-5',  # 평일 18시
    catchup=False
) as dag:
    # 상장기업의 일간 공시 수집
    fetch_disclosures_task = PythonOperator(
        task_id='fetch_disclosures',
        python_callable=run_fetch_disclosures,
        op_kwargs={
            'report_group': 'daily',
            'only_listed': True  # 상장기업만
        },
    )
    
    fetch_disclosures_task 
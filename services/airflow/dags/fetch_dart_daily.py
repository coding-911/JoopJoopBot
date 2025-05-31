from airflow import DAG
from airflow.operators.python import PythonOperator

from dart_common import (
    default_args,
    run_fetch_corps,
    run_fetch_disclosures
)

with DAG(
    'fetch_dart_daily',
    default_args=default_args,
    description='DART 데이터 일일 수집 (주요사항/경영진 변경)',
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
        op_kwargs={
            'corp_codes': "{{ task_instance.xcom_pull(task_ids='fetch_corps') }}",
            'report_group': 'daily'
        },
    )
    
    fetch_corps_task >> fetch_disclosures_task 
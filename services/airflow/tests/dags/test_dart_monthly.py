import os
import pytest
from datetime import datetime, timedelta
from airflow.models import DagBag
from airflow.utils.dates import days_ago

# DAG 파일 경로 설정
DAG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dags")
DAG_FILE = "dart_monthly.py"

class TestDartMonthlyDag:
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 환경 설정"""
        self.dagbag = DagBag(dag_folder=DAG_PATH, include_examples=False)
    
    def test_dag_loaded(self):
        """DAG 로드 테스트"""
        assert self.dagbag.import_errors == {}
        assert f"{DAG_FILE}" in self.dagbag.dag_ids
    
    def test_dag_structure(self):
        """DAG 구조 테스트"""
        dag = self.dagbag.get_dag(dag_id="dart_monthly")
        assert dag is not None
        
        # 태스크 존재 확인
        tasks = dag.tasks
        task_ids = [task.task_id for task in tasks]
        
        expected_tasks = [
            "update_corps",
            "get_listed_corps",
            "collect_monthly_disclosures",
            "process_documents"
        ]
        
        for task_id in expected_tasks:
            assert task_id in task_ids
    
    def test_dependencies(self):
        """태스크 의존성 테스트"""
        dag = self.dagbag.get_dag(dag_id="dart_monthly")
        
        # update_corps -> get_listed_corps
        listed_corps_task = dag.get_task("get_listed_corps")
        assert dag.get_task("update_corps").task_id in [
            task.task_id for task in listed_corps_task.upstream_list
        ]
        
        # get_listed_corps -> collect_monthly_disclosures
        collect_task = dag.get_task("collect_monthly_disclosures")
        assert listed_corps_task.task_id in [
            task.task_id for task in collect_task.upstream_list
        ]
        
        # collect_monthly_disclosures -> process_documents
        process_task = dag.get_task("process_documents")
        assert collect_task.task_id in [
            task.task_id for task in process_task.upstream_list
        ]
    
    def test_default_args(self):
        """기본 설정 테스트"""
        dag = self.dagbag.get_dag(dag_id="dart_monthly")
        
        assert dag.default_args["owner"] == "joopjoop"
        assert dag.default_args["retries"] == 3
        assert isinstance(dag.default_args["retry_delay"], timedelta)
    
    def test_schedule_interval(self):
        """스케줄링 설정 테스트"""
        dag = self.dagbag.get_dag(dag_id="dart_monthly")
        
        # 매월 1일 오전 9시(KST) 실행
        assert dag.schedule_interval == "0 0 1 * *"  # UTC 기준
        
        # 시작 날짜가 과거로 설정되어 있는지 확인
        assert dag.start_date <= days_ago(30) 
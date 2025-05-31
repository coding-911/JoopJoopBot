import os
import pytest
from datetime import datetime, timedelta
from airflow.models import DagBag
from airflow.utils.dates import days_ago

# DAG 파일 경로 설정
DAG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dags")
DAG_FILE = "dart_daily.py"

class TestDartDailyDag:
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
        dag = self.dagbag.get_dag(dag_id="dart_daily")
        assert dag is not None
        
        # 태스크 존재 확인
        tasks = dag.tasks
        task_ids = [task.task_id for task in tasks]
        
        expected_tasks = [
            "get_listed_corps",
            "collect_daily_disclosures",
            "process_documents"
        ]
        
        for task_id in expected_tasks:
            assert task_id in task_ids
    
    def test_dependencies(self):
        """태스크 의존성 테스트"""
        dag = self.dagbag.get_dag(dag_id="dart_daily")
        
        # get_listed_corps -> collect_daily_disclosures
        collect_task = dag.get_task("collect_daily_disclosures")
        assert dag.get_task("get_listed_corps").task_id in [
            task.task_id for task in collect_task.upstream_list
        ]
        
        # collect_daily_disclosures -> process_documents
        process_task = dag.get_task("process_documents")
        assert collect_task.task_id in [
            task.task_id for task in process_task.upstream_list
        ]
    
    def test_default_args(self):
        """기본 설정 테스트"""
        dag = self.dagbag.get_dag(dag_id="dart_daily")
        
        assert dag.default_args["owner"] == "joopjoop"
        assert dag.default_args["retries"] == 3
        assert isinstance(dag.default_args["retry_delay"], timedelta)
    
    def test_schedule_interval(self):
        """스케줄링 설정 테스트"""
        dag = self.dagbag.get_dag(dag_id="dart_daily")
        
        # 매일 오전 9시(KST) 실행
        assert dag.schedule_interval == "0 0 * * *"  # UTC 기준
        
        # 시작 날짜가 과거로 설정되어 있는지 확인
        assert dag.start_date <= days_ago(1) 
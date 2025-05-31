# Airflow DAG 실행 가이드

이 문서는 JoopJoopBot의 Airflow DAG 실행 방법을 설명합니다.

## 사전 준비사항

### 1. 환경 변수 설정
```bash
# 필수 환경 변수
DART_API_KEY=your_dart_api_key
VECTOR_DB_PATH=/opt/airflow/vector_store  # 기본값, 변경 가능

# 선택적 환경 변수
AIRFLOW_ALERT_EMAIL=your_email@example.com  # 알림 이메일
AIRFLOW_TASK_RETRIES=3  # 재시도 횟수
AIRFLOW_RETRY_DELAY_MINUTES=5  # 재시도 간격(분)
```

### 2. 의존성 설치
```bash
pip install apache-airflow
pip install -e .  # 프로젝트 루트 디렉토리에서 실행
```

> **참고**: Docker Compose로 Airflow를 실행하는 경우, 위 의존성은 이미 컨테이너에 설치되어 있으므로 별도 설치가 필요하지 않습니다.

## CLI를 통한 실행 방법

1. DAG 목록 확인
```bash
# Airflow 디렉토리로 이동
cd services/airflow

# DAG 목록 조회
airflow dags list  # 로컬 실행시
# docker compose exec airflow-webserver airflow dags list  # Docker Compose 환경
```

2. DAG 상태 확인
```bash
airflow dags show fetch_dart_historical  # 로컬 실행시
# docker compose exec airflow-webserver airflow dags show fetch_dart_historical  # Docker Compose 환경
```

3. DAG 실행
```bash
# 단순 실행
airflow dags trigger fetch_dart_historical  # 로컬 실행시
# docker compose exec airflow-webserver airflow dags trigger fetch_dart_historical  # Docker Compose 환경

# 특정 설정으로 실행 (예: 날짜 지정)
airflow dags trigger fetch_dart_historical --conf '{"start_date": "20230101", "end_date": "20231231"}'  # 로컬 실행시
# docker compose exec airflow-webserver airflow dags trigger fetch_dart_historical --conf '{"start_date": "20230101", "end_date": "20231231"}'  # Docker Compose 환경
```

4. 실행 상태 확인
```bash
airflow dags state fetch_dart_historical run_id  # 로컬 실행시
# docker compose exec airflow-webserver airflow dags state fetch_dart_historical run_id  # Docker Compose 환경
```

## Airflow UI를 통한 실행 방법

1. Airflow 웹서버 실행
```bash
# 기본 포트(8080)로 실행
airflow webserver

# 특정 포트로 실행
airflow webserver -p 8085
```

> **참고**: Docker Compose로 Airflow를 실행하는 경우, 웹서버가 이미 실행 중이므로 위 단계는 생략합니다.
> Docker Compose 환경에서는 기본적으로 `localhost:8080`으로 접속 가능합니다.

2. UI 접속
- 웹 브라우저에서 `http://localhost:8080` (또는 지정한 포트) 접속
- 기본 계정: airflow/airflow

3. DAG 실행하기
   1. DAGs 메뉴에서 `fetch_dart_historical` DAG 클릭
   2. Actions 메뉴에서 "Trigger DAG" 버튼 클릭
   3. 필요한 경우 Configuration JSON에 파라미터 입력
   ```json
   {
     "start_date": "20230101",
     "end_date": "20231231"
   }
   ```
   4. "Trigger" 버튼 클릭

4. 모니터링
   - Grid View: 전체 태스크 실행 현황 확인
   - Graph View: DAG 구조와 태스크 상태 시각적 확인
   - Task Instance Details: 각 태스크의 로그와 상태 확인

## 주의사항

1. 실행 전 확인사항
   - 환경 변수가 올바르게 설정되었는지 확인
   - DART API 키가 유효한지 확인
   - 벡터 DB 저장 경로가 존재하고 쓰기 권한이 있는지 확인

2. 문제 해결
   - 로그 확인: 
     ```bash
     airflow tasks logs fetch_dart_historical task_id execution_date  # 로컬 실행시
     # docker compose exec airflow-webserver airflow tasks logs fetch_dart_historical task_id execution_date  # Docker Compose 환경
     ```
   - 태스크 재실행: 
     ```bash
     airflow tasks clear fetch_dart_historical -t task_id -s execution_date  # 로컬 실행시
     # docker compose exec airflow-webserver airflow tasks clear fetch_dart_historical -t task_id -s execution_date  # Docker Compose 환경
     ```

3. 리소스 관리
   - 대량의 기업 데이터를 수집하므로 디스크 공간 모니터링 필요
   - 벡터 DB 크기가 커질 수 있으므로 주기적인 관리 필요 
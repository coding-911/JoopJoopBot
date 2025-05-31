# Airflow DAG 테스트 가이드

## 테스트 실행 환경 설정

### 1. 기본 설정

```bash
# 1. 프로젝트 루트로 이동
cd C:\study\JoopJoop\JoopJoopBot

# 2. Airflow 서비스 디렉토리로 이동
cd services/airflow

# 3. 의존성 설치
poetry install

# 4. 환경변수 설정 (.env 파일이 없는 경우)
echo "DART_API_KEY=your_api_key_here" > .env
```

## 테스트 실행 명령어

### 1. 전체 DAG 테스트

```bash
# 모든 DAG 테스트 실행
poetry run pytest tests/dags/
```

### 2. 개별 DAG 테스트

```bash
# 일간 DAG 테스트
poetry run pytest tests/dags/test_dart_daily.py

# 주간 DAG 테스트
poetry run pytest tests/dags/test_dart_weekly.py

# 월간 DAG 테스트
poetry run pytest tests/dags/test_dart_monthly.py
```

### 3. 마커별 테스트

```bash
# 일간 테스트
poetry run pytest -m daily tests/dags/

# 주간 테스트
poetry run pytest -m weekly tests/dags/

# 월간 테스트
poetry run pytest -m monthly tests/dags/
```

## 주의사항

1. Windows 환경에서는 경로 구분자로 `/`를 사용해도 됩니다.
2. 환경변수는 시스템 환경변수로도 설정 가능합니다.
3. `pip` 환경에서는 `poetry run` 없이 실행 가능합니다.
4. 테스트 실행 전 의존성 최신 상태를 확인하세요.
5. Airflow 설정이 올바르게 되어 있는지 확인하세요. 
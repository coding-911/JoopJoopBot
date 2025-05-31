# 전체 테스트 실행 가이드

## 테스트 실행 환경 설정

### 1. 기본 설정

```bash
# 1. 프로젝트 루트로 이동
cd C:\study\JoopJoop\JoopJoopBot

# 2. 의존성 설치
poetry install
```

## 테스트 실행 명령어

### 1. 전체 테스트 실행

```bash
# 모든 테스트 실행
poetry run pytest packages/joopjoop-core/tests/ services/airflow/tests/
```

### 2. 상세 로그 테스트

```bash
# 상세 로그와 함께 실행
poetry run pytest -v packages/joopjoop-core/tests/ services/airflow/tests/
```

### 3. 실패 테스트 재실행

```bash
# 실패한 테스트만 실행
poetry run pytest --lf packages/joopjoop-core/tests/ services/airflow/tests/
```

### 4. 커버리지 리포트

```bash
# 테스트 커버리지 리포트 생성
poetry run pytest --cov=joopjoop packages/joopjoop-core/tests/ services/airflow/tests/ --cov-report=html
```

## 주의사항

1. Windows 환경에서는 경로 구분자로 `/`를 사용해도 됩니다.
2. 환경변수는 시스템 환경변수로도 설정 가능합니다.
3. `pip` 환경에서는 `poetry run` 없이 실행 가능합니다.
4. 테스트 실행 전 의존성 최신 상태를 확인하세요.
5. 커버리지 리포트는 `htmlcov` 디렉토리에 생성됩니다. 
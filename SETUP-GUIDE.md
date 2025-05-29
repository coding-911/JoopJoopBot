# JoopJoop Bot 설정 가이드

## 사전 요구사항

- Docker Desktop
- Python 3.11+
- Node.js 18+
- Poetry (Python 패키지 관리자)
- pnpm (Node.js 패키지 관리자)

## 프로젝트 구조

```
JoopJoopBot/
├── packages/
│   └── joopjoop-core/      # 공통 코드 패키지
├── services/
│   ├── airflow/            # Airflow 서비스
│   │   ├── dags/          # Airflow DAG 파일들
│   │   └── Dockerfile     # Airflow 컨테이너 설정
│   ├── api/               # 백엔드 API 서비스
│   └── web/               # 프론트엔드 서비스
└── docker-compose.yaml     # 전체 서비스 구성
```

## 1. 기본 환경 설정

### 1.1 Python 3.11 설치 (Ubuntu/WSL)
```bash
# Python 3.11 저장소 추가 및 설치
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# pip 설치 (Python 3.11용)
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Poetry 설치 (Python 3.11로)
curl -sSL https://install.python-poetry.org | python3.11 -
```

### 1.2 Node.js 및 pnpm 설치
```bash
# Node.js 18.x 설치
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# pnpm 설치
npm install -g pnpm
```

## 2. 환경 변수 설정

루트 디렉토리에 .env 파일 생성:
```bash
# 서비스 포트 설정
API_PORT=8000
VITE_PORT=5173
POSTGRES_PORT=5432
AIRFLOW_PORT=8080
REDIS_PORT=6379
GRAFANA_PORT=3000

# DART API 설정
DART_API_KEY=your_dart_api_key_here

# 데이터베이스 설정
POSTGRES_USER=joopjoop
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_postgres_db
POSTGRES_HOST=db

# 벡터 DB 설정
VECTOR_DB_PATH=/app/data/vector_store

# Airflow 설정
AIRFLOW_UID=50000
AIRFLOW__CORE__LOAD_EXAMPLES=false
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW__WEBSERVER__SECRET_KEY=your-secret-key-here
AIRFLOW_ALERT_EMAIL=your-email@example.com
AIRFLOW_TASK_RETRIES=1
AIRFLOW_RETRY_DELAY_MINUTES=5
```

### 환경 변수 설명

1. **서비스 포트**
   - `API_PORT`: FastAPI 서버 포트 (기본값: 8000)
   - `VITE_PORT`: 프론트엔드 개발 서버 포트 (기본값: 5173)
   - `POSTGRES_PORT`: PostgreSQL 포트 (기본값: 5432)
   - `AIRFLOW_PORT`: Airflow 웹 UI 포트 (기본값: 8080)
   - `REDIS_PORT`: Redis 캐시 서버 포트 (기본값: 6379)
   - `GRAFANA_PORT`: Grafana 대시보드 포트 (기본값: 3000)

2. **DART API**
   - `DART_API_KEY`: DART OpenAPI 인증키 (필수)

3. **데이터베이스**
   - `POSTGRES_USER`: PostgreSQL 사용자명
   - `POSTGRES_PASSWORD`: PostgreSQL 비밀번호
   - `POSTGRES_DB`: 데이터베이스 이름
   - `POSTGRES_HOST`: 데이터베이스 호스트

4. **벡터 DB**
   - `VECTOR_DB_PATH`: 벡터 DB 저장 경로
     - API 서비스: /app/data/vector_store
     - Airflow: /opt/airflow/vector_store

5. **Airflow**
   - `AIRFLOW_UID`: Airflow 사용자 ID
   - `AIRFLOW_ALERT_EMAIL`: 알림 수신 이메일
   - `AIRFLOW_TASK_RETRIES`: 작업 재시도 횟수
   - `AIRFLOW_RETRY_DELAY_MINUTES`: 재시도 간격(분)

## 3. 서비스 설정 및 실행

### 3.1 코어 패키지 설치
```bash
cd packages/joopjoop-core
poetry env use python3.11
poetry install
poetry build
cd ../..
```

### 3.2 서비스별 의존성 설치
```bash
# API 서버
cd services/api
poetry env use python3.11
poetry install
cd ../..

# 프론트엔드
cd services/web
pnpm install
cd ../..
```

### 3.3 Docker 서비스 실행
```bash
# 전체 서비스 빌드 및 시작
docker compose up --build -d

# 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f
```

## 4. 서비스 접속 정보

- API 서버: http://localhost:8000
  - API 문서: http://localhost:8000/docs
- 프론트엔드: http://localhost:3000
- Airflow 웹 UI: http://localhost:8080 (기본 계정: airflow / airflow)

## 5. 문제 해결 가이드

### Docker 관련 문제
```bash
# 컨테이너 상태 확인
docker compose ps

# 특정 서비스 로그 확인
docker compose logs -f [서비스명]

# 특정 서비스 재시작
docker compose restart [서비스명]

# 전체 재빌드
docker compose down
docker compose up --build -d
```

### Poetry 관련 문제
- Permission 에러: `sudo` 사용 또는 사용자 권한 확인
- 환경 문제: `poetry env list` 로 현재 환경 확인
- 캐시 정리: `poetry cache clear . --all`

## 6. 개발 시 유의사항

1. 코어 패키지 수정 시
   - `packages/joopjoop-core`에서 수정 후 `poetry install`

2. API 엔드포인트 추가 시
   - `services/api/src/joopjoop_api/routers/` 디렉토리에 라우터 추가
   - `main.py`에 라우터 등록

3. DAG 개발 시
   - `services/airflow/dags/` 디렉토리에 DAG 추가
   - Python 패키지 추가 시 `services/airflow/requirements.txt` 수정 
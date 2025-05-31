# JoopJoop Bot 설정 가이드

## 사전 요구사항

- Docker Desktop
- Python 3.11+
- Node.js 18+
- Poetry (Python 패키지 관리자)

## 프로젝트 구조

```
JoopJoopBot/
├── packages/
│   └── joopjoop-core/      # 공통 코드 패키지
├── services/
│   ├── airflow/            # Airflow 서비스
│   │   ├── dags/          # Airflow DAG 파일들
│   │   └── Dockerfile     # Airflow 컨테이너 설정
│   ├── backend/           # 백엔드 API 서비스
│   │   └── Dockerfile     # 백엔드 컨테이너 설정
│   └── frontend/          # 프론트엔드 서비스
│       └── Dockerfile     # 프론트엔드 컨테이너 설정
├── docker-compose.yaml     # 전체 서비스 구성
└── pyproject.toml         # Poetry 프로젝트 설정
```

## 1. 기본 환경 설정

### 1.1 Python 3.11 설치

#### Windows
1. [Python 3.11 공식 사이트](https://www.python.org/downloads/)에서 설치
2. 설치 시 "Add Python to PATH" 옵션 선택

#### Ubuntu/WSL
```bash
# Python 3.11 저장소 추가 및 설치
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# pip 설치 (Python 3.11용)
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
```

### 1.2 Poetry 설치

#### Windows (PowerShell)
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

#### Ubuntu/WSL
```bash
curl -sSL https://install.python-poetry.org | python3.11 -
```

### 1.3 Node.js 설치

#### Windows
1. [Node.js 18.x LTS 버전](https://nodejs.org/) 다운로드 및 설치

#### Ubuntu/WSL
```bash
# Node.js 18.x 설치
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 2. 프로젝트 설정

### 2.1 프로젝트 클론
```bash
git clone https://github.com/your-username/JoopJoopBot.git
cd JoopJoopBot
```

### 2.2 Poetry 환경 설정
```bash
# Poetry 가상 환경 생성 및 의존성 설치
poetry install

# 가상 환경 활성화
poetry shell
```

### 2.3 환경 변수 설정

`.env` 파일 생성:
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
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=joopjoop
POSTGRES_HOST=postgres

# Redis 설정
REDIS_PASSWORD=your_redis_password

# 벡터 DB 설정
VECTOR_DB_PATH=/app/data/vector_store

# Airflow 설정
AIRFLOW_UID=50000
AIRFLOW__CORE__LOAD_EXAMPLES=false
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW__WEBSERVER__SECRET_KEY=your_secure_secret_key
```

## 3. 서비스 실행

### 3.1 Docker 서비스 실행
```bash
# 전체 서비스 빌드 및 시작
docker compose up --build -d

# 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f
```

### 3.2 서비스 접속

- 백엔드 API: http://localhost:8000
  - Swagger 문서: http://localhost:8000/docs
- 프론트엔드: http://localhost:5173
- Airflow: http://localhost:8080
  - 기본 계정: airflow / airflow
- Grafana: http://localhost:3000
  - 기본 계정: admin / admin

## 4. 개발 가이드

### 4.1 백엔드 개발
```bash
cd services/backend

# 의존성 설치
poetry install

# 개발 서버 실행
poetry run uvicorn app.main:app --reload
```

### 4.2 프론트엔드 개발
```bash
cd services/frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 4.3 Airflow DAG 개발
- `services/airflow/dags/` 디렉토리에 DAG 파일 추가
- Python 패키지 추가 시 `services/airflow/requirements.txt` 수정

## 5. 문제 해결

### 5.1 Docker 관련 문제
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

### 5.2 Poetry 관련 문제
- 가상 환경 확인: `poetry env list`
- 캐시 정리: `poetry cache clear . --all`
- 의존성 업데이트: `poetry update`

### 5.3 데이터베이스 관련 문제
```bash
# PostgreSQL 컨테이너 접속
docker compose exec postgres psql -U joopjoop -d joopjoop

# 데이터베이스 초기화
docker compose down -v
docker compose up -d
```

## 6. 배포 가이드

### 6.1 프로덕션 환경 설정
- `.env.prod` 파일 생성
- 보안 관련 환경 변수 설정
  - `POSTGRES_PASSWORD`
  - `REDIS_PASSWORD`
  - `AIRFLOW__WEBSERVER__SECRET_KEY`
  - `GRAFANA_ADMIN_PASSWORD`

### 6.2 프로덕션 배포
```bash
# 프로덕션 환경 변수 사용
cp .env.prod .env

# 서비스 실행
docker compose -f docker-compose.prod.yaml up -d
``` 
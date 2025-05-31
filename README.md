# JoopJoop Bot

주식 관련 공시 정보를 수집하고 분석하는 AI 봇 프로젝트

## 프로젝트 구조

```
.
├── packages/                # 공통 패키지
│   └── joopjoop-core/      # 코어 기능 (DART API, RAG)
├── services/               # 서비스
│   ├── backend/           # FastAPI 백엔드
│   ├── frontend/          # React 프론트엔드
│   └── airflow/           # Airflow DAGs
├── docs/                  # 프로젝트 문서
└── pr/                    # PR 관련 문서
```

## 주요 기능

- DART API를 통한 기업 공시 정보 수집
- RAG(Retrieval Augmented Generation) 기반 문서 처리
- 실시간 공시 모니터링 및 알림
- 공시 내용 분석 및 요약
- Grafana 기반 모니터링 대시보드

## 시작하기

1. 사전 요구사항
   - Docker Desktop
   - Python 3.11+
   - Poetry (Python 패키지 관리자)
   - Node.js 18+

2. 환경 설정
```bash
# 환경 변수 설정
cp .env.example .env
# 환경 변수 편집
```

3. 개발 환경 실행
```bash
# Poetry 의존성 설치
poetry install

# Docker 서비스 실행
docker-compose up -d
```

자세한 설정 방법은 [SETUP-GUIDE.md](SETUP-GUIDE.md)를 참조하세요.

## 서비스 접속 정보

- 백엔드 API: http://localhost:8000
  - Swagger 문서: http://localhost:8000/docs
- 프론트엔드: http://localhost:5173
- Airflow: http://localhost:8080
- Grafana: http://localhost:3000

## 환경 변수

필수 환경변수:
- `DART_API_KEY`: DART OpenAPI 인증키
- `VECTOR_DB_PATH`: 벡터 DB 저장 경로
- `POSTGRES_PASSWORD`: PostgreSQL 비밀번호
- `AIRFLOW__WEBSERVER__SECRET_KEY`: Airflow 웹서버 시크릿 키

자세한 환경 변수 설정은 [SETUP-GUIDE.md](SETUP-GUIDE.md)를 참조하세요.

## 라이선스

MIT License 
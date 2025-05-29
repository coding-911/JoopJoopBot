# JoopJoop Bot

주식 관련 공시 정보를 수집하고 분석하는 AI 봇 프로젝트

## 프로젝트 구조

```
.
├── packages/                # 공통 패키지
│   └── joopjoop-core/      # 코어 기능 (DART API, RAG)
├── services/               # 서비스
│   ├── api/               # FastAPI 백엔드
│   ├── web/               # React 프론트엔드
│   └── airflow/           # Airflow DAGs
├── docker/                # Docker 설정
│   ├── development/       # 개발 환경
│   └── production/        # 운영 환경
└── docs/                  # 프로젝트 문서
```

## 주요 기능

- DART API를 통한 기업 공시 정보 수집
- RAG(Retrieval Augmented Generation) 기반 문서 처리
- 실시간 공시 모니터링 및 알림
- 공시 내용 분석 및 요약

## 시작하기

1. 환경 설정
```bash
# 환경 변수 설정
cp .env.example .env
# 환경 변수 편집
```

2. 개발 환경 실행
```bash
docker-compose up -d
```

자세한 설정 방법은 [SETUP_GUIDE.md](SETUP_GUIDE.md)를 참조하세요.

## 환경 변수

필수 환경변수:
- `DART_API_KEY`: DART OpenAPI 인증키
- `VECTOR_DB_PATH`: 벡터 DB 저장 경로

## 라이선스

MIT License 
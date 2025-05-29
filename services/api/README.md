# JoopJoop API Service

JoopJoop 프로젝트의 FastAPI 기반 백엔드 서비스입니다.

## 기능

- DART API 엔드포인트
- 공시 데이터 검색 및 조회
- RAG 파이프라인 연동

## 설치

```bash
# Poetry 환경 설정
poetry env use python3.11

# 의존성 설치
poetry install
```

## 실행

```bash
# 개발 서버 실행
poetry run uvicorn src.joopjoop_api.main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:18000/docs
- ReDoc: http://localhost:18000/redoc 
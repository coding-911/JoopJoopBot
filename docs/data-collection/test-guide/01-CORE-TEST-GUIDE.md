# 코어 패키지 테스트 가이드

## 테스트 실행 환경 설정

### 1. 기본 설정

```bash
# 1. 프로젝트 루트로 이동
cd C:\study\JoopJoop\JoopJoopBot

# 2. 코어 패키지 디렉토리로 이동
cd packages/joopjoop-core

# 3. 의존성 설치
poetry install

# 4. 환경변수 설정 (.env 파일이 없는 경우)
echo "DART_API_KEY=your_api_key_here" > .env
```

## 테스트 실행 명령어

### 1. 전체 테스트

```bash
# 모든 테스트 실행
poetry run pytest tests/
```

### 2. DART 관련 테스트

```bash
# DART 관련 모든 테스트
poetry run pytest tests/dart/

# 증분 수집 테스트
DART_TEST_MODE=incremental poetry run pytest tests/dart/test_dart_collection.py

# 초기 수집 테스트
DART_TEST_MODE=initial poetry run pytest tests/dart/test_dart_collection.py

# 기업 정보 관리 테스트
poetry run pytest tests/dart/test_corp_manager.py
```

### 3. RAG 관련 테스트

```bash
# RAG 관련 모든 테스트
poetry run pytest tests/rag/

# RAG 파이프라인 테스트
poetry run pytest tests/rag/test_pipeline.py
```

## 주의사항

1. Windows 환경에서는 경로 구분자로 `/`를 사용해도 됩니다.
2. 환경변수는 시스템 환경변수로도 설정 가능합니다.
3. `pip` 환경에서는 `poetry run` 없이 실행 가능합니다.
4. 테스트 실행 전 의존성 최신 상태를 확인하세요. 
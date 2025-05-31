# DART 데이터 수집 테스트 가이드

## 개요

DART 데이터 수집 테스트는 다음과 같은 영역을 포함합니다:

1. 코어 패키지 테스트 (`packages/joopjoop-core/tests/`)
   - 기업 정보 관리 테스트 (CorpManager)
   - 공시 수집 테스트 (DART API)
   - RAG 파이프라인 테스트

2. Airflow DAG 테스트 (`services/airflow/tests/`)
   - 일간 DAG 테스트
   - 주간 DAG 테스트
   - 월간 DAG 테스트

## 테스트 가이드 문서

각 영역별 상세한 테스트 실행 방법은 다음 문서들을 참조하세요:

1. [코어 패키지 테스트 가이드](./01-CORE-TEST-GUIDE.md)
   - 기업 정보 관리 테스트
   - DART 데이터 수집 테스트
   - RAG 파이프라인 테스트

2. [Airflow DAG 테스트 가이드](./02-AIRFLOW-TEST-GUIDE.md)
   - 일간/주간/월간 DAG 테스트
   - 마커별 테스트 실행

3. [전체 테스트 실행 가이드](./03-FULL-TEST-GUIDE.md)
   - 통합 테스트 실행
   - 커버리지 리포트 생성

## 테스트 환경 설정

### 1. 환경변수 설정

`.env` 파일에 다음 환경변수를 설정합니다:

```bash
DART_API_KEY=your_api_key_here
DART_TEST_MODE=incremental  # 또는 initial
```

### 2. 테스트 실행

```bash
# 코어 패키지 테스트
cd packages/joopjoop-core
poetry install  # 의존성 설치
poetry run pytest tests/  # 전체 테스트
poetry run pytest tests/dart/  # DART 관련 테스트만
poetry run pytest tests/rag/   # RAG 관련 테스트만

# Airflow DAG 테스트
cd services/airflow
poetry install  # 의존성 설치
poetry run pytest tests/dags/  # 전체 DAG 테스트
```

## 테스트 모듈 설명

### 1. 코어 패키지 테스트

#### A. 기업 정보 관리 테스트 (`test_corp_manager.py`)

기업 정보를 SQLite DB로 관리하는 `CorpManager` 클래스의 기능을 테스트합니다.

##### 테스트 케이스:

1. **DB 초기화 테스트**
   - DB 파일 생성 확인
   - 테이블 및 스키마 검증

2. **기업 정보 업데이트 테스트**
   - DART API 기업 목록 조회
   - DB 업데이트 및 저장
   - 샘플 기업(삼성전자) 정보 검증

3. **상장기업 조회 테스트**
   - 상장/비상장 기업 구분
   - 상장기업 필터링

4. **CRUD 작업 테스트**
   - 기업 정보 생성/조회/수정/삭제

5. **수집 시간 추적 테스트**
   - 초기/업데이트 시간 관리
   - 시간 추적 정확성 검증

#### B. 공시 수집 테스트 (`test_dart_collection.py`)

##### 증분 수집 테스트 (incremental)

- **대상 기업**: 
  - 삼성전자, 현대자동차, SK하이닉스, 카카오

- **수집 주기별 테스트**:
  - 일간 수집 (1일)
  - 주간 수집 (7일)
  - 월간 수집 (30일)

##### 초기 수집 테스트 (initial)

- **대상 기업**: 삼성전자 (단일 기업)
- **수집 기간**: 최근 1년
- **수집 대상**: 모든 보고서 타입

#### C. RAG 파이프라인 테스트 (`test_pipeline.py`)

1. **문서 처리 테스트**
   - 문서 청크 분할
   - 임베딩 생성
   - 벡터 DB 저장

2. **검색 기능 테스트**
   - 키워드 기반 검색
   - 기업별 필터링
   - 관련성 순위 확인

3. **메타데이터 필터링 테스트**
   - 보고서 타입별 필터링
   - 수집 그룹별 필터링

### 2. Airflow DAG 테스트

#### A. 일간 DAG 테스트 (`test_dart_daily.py`)

1. **DAG 구조 테스트**
   - 태스크 존재 확인
   - 태스크 의존성 검증

2. **스케줄링 테스트**
   - 매일 오전 9시(KST) 실행
   - 시작 날짜 설정 확인

#### B. 주간 DAG 테스트 (`test_dart_weekly.py`)

1. **DAG 구조 테스트**
   - 태스크 존재 확인
   - 태스크 의존성 검증

2. **스케줄링 테스트**
   - 매주 월요일 오전 9시(KST) 실행
   - 시작 날짜 설정 확인

#### C. 월간 DAG 테스트 (`test_dart_monthly.py`)

1. **DAG 구조 테스트**
   - 태스크 존재 확인
   - 태스크 의존성 검증

2. **스케줄링 테스트**
   - 매월 1일 오전 9시(KST) 실행
   - 시작 날짜 설정 확인

## 테스트 프로세스

### 1. 임시 저장소 관리

모든 테스트는 임시 디렉토리에서 실행되며, 테스트 종료 후 자동으로 정리됩니다:
- SQLite DB 파일 (`test.db`)
- 벡터 DB 디렉토리 (`vector_store/`)

### 2. 오류 처리 및 로깅

- 각 단계별 상세한 오류 로깅
- 개별 테스트 실패시에도 전체 테스트는 계속 진행
- 임시 파일 정리 실패시 경고 메시지 출력

## 주의사항

1. **API 호출 제한**
   - DART OpenAPI의 호출 제한을 고려하여 설계됨
   - 테스트시 최대 10개 공시로 제한

2. **테스트 격리**
   - 각 테스트는 독립적인 임시 디렉토리 사용
   - 테스트간 상호 영향 없음

3. **환경 설정**
   - `.env` 파일 필수
   - 적절한 API 키 설정 필요

## 문제 해결

일반적인 문제 및 해결 방법:

1. **DART_API_KEY 오류**
   - `.env` 파일 존재 여부 확인
   - API 키 유효성 확인

2. **의존성 문제**
   - 각 패키지 디렉토리에서 `poetry install` 실행
   - 가상환경 활성화 확인

3. **임시 디렉토리 오류**
   - 디스크 공간 확인
   - 권한 설정 확인

4. **DAG 테스트 오류**
   - Airflow 설정 확인
   - DAG 파일 존재 여부 확인
   - 의존성 설치 확인 
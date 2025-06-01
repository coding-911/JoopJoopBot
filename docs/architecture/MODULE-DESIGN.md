# JoopJoop 모듈 설계

## 1. 프로젝트 구조

```
JoopJoopBot/
├── services/               # 마이크로서비스
│   ├── backend/           # API 서버
│   ├── web/              # 프론트엔드
│   └── airflow/          # 데이터 파이프라인
├── packages/              # 공유 패키지
│   └── joopjoop-core/    # 코어 라이브러리
├── scripts/              # 유틸리티 스크립트
├── docs/                 # 문서
└── data/                 # 데이터 저장소
```

## 2. 서비스별 모듈 구조

### 2.1 Backend (API 서버)

```
backend/
├── app/
│   ├── api/              # API 라우터
│   ├── core/             # 핵심 설정
│   ├── crud/             # 데이터베이스 작업
│   ├── db/               # 데이터베이스 설정
│   ├── models/           # 데이터베이스 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── services/         # 비즈니스 로직
│   └── tests/            # 테스트
├── Dockerfile
└── requirements.txt
```

#### 주요 모듈
- **api**: REST API 엔드포인트 정의
- **core**: 설정, 상수, 유틸리티
- **services**: 비즈니스 로직 구현
- **models**: SQLAlchemy 모델
- **schemas**: 데이터 검증 스키마

### 2.2 Web (프론트엔드)

```
web/
├── src/
│   ├── components/       # React 컴포넌트
│   ├── pages/           # 페이지 컴포넌트
│   ├── hooks/           # 커스텀 훅
│   ├── services/        # API 통신
│   ├── store/           # 상태 관리
│   ├── styles/          # 스타일시트
│   └── utils/           # 유틸리티
├── public/              # 정적 파일
├── Dockerfile
└── package.json
```

#### 주요 모듈
- **components**: 재사용 가능한 UI 컴포넌트
- **pages**: 라우트별 페이지 컴포넌트
- **services**: API 클라이언트 및 통신 로직
- **store**: 전역 상태 관리
- **hooks**: 공통 로직 추상화

### 2.3 Airflow (데이터 파이프라인)

```
airflow/
├── dags/                # DAG 정의
│   ├── dart/           # DART 데이터 수집
│   ├── preprocessing/  # 데이터 전처리
│   └── monitoring/     # 모니터링
├── tests/              # 테스트
├── plugins/             # 커스텀 플러그인
├── logs/               # 로그 파일
├── Dockerfile
└── requirements.txt
```

#### 주요 모듈
- **dags**: 워크플로우 정의
- **plugins**: 커스텀 오퍼레이터, 훅
- **config**: Airflow 설정

### 2.4 JoopJoop Core (공유 라이브러리)

```
joopjoop-core/
├── src/
│   └── joopjoop/
│       ├── dart/       # DART API 클라이언트
│       ├── db/         # 데이터베이스 유틸리티
│       ├── models/     # 공통 모델
│       └── utils/      # 공통 유틸리티
├── tests/              # 테스트
└── setup.py
```

#### 주요 모듈
- **dart**: DART API 통신 및 데이터 처리
- **db**: 데이터베이스 연결 및 쿼리
- **models**: 공통 데이터 모델
- **utils**: 공통 유틸리티 함수

## 3. 모듈 간 의존성

### 3.1 서비스 의존성
- **Backend** → JoopJoop Core
- **Airflow** → JoopJoop Core
- **Web** → Backend API

### 3.2 데이터 의존성
- **Backend** → PostgreSQL, Redis, Vector DB
- **Airflow** → PostgreSQL, Vector DB
- **Grafana** → PostgreSQL

## 4. 모듈 설계 원칙

### 4.1 설계 패턴
- Repository 패턴: 데이터 액세스 추상화
- Factory 패턴: 객체 생성 로직 캡슐화
- Strategy 패턴: 알고리즘 교체 가능성
- Observer 패턴: 이벤트 기반 통신

### 4.2 SOLID 원칙
- 단일 책임 원칙 (SRP)
- 개방-폐쇄 원칙 (OCP)
- 인터페이스 분리 원칙 (ISP)
- 의존성 역전 원칙 (DIP)

### 4.3 코드 구성
- 관심사 분리
- 모듈화 및 재사용성
- 테스트 용이성
- 확장 가능성

## 5. 테스트 전략

### 5.1 테스트 수준
- 단위 테스트: 개별 모듈
- 통합 테스트: 모듈 간 상호작용
- E2E 테스트: 전체 시스템

### 5.2 테스트 도구
- Backend: pytest
- Frontend: Jest, React Testing Library
- Core: pytest
- E2E: Cypress

## 6. 모니터링 및 로깅

### 6.1 메트릭 수집
- 서비스별 성능 메트릭
- 데이터베이스 메트릭
- 시스템 리소스 사용량

### 6.2 로그 관리
- 구조화된 로깅
- 로그 레벨 구분
- 중앙 집중식 로그 수집 
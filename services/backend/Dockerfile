# Builder stage
FROM python:3.11-slim as builder

WORKDIR /build

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install --no-cache-dir poetry

# joopjoop-core 패키지 복사
COPY packages/joopjoop-core /packages/joopjoop-core
RUN cd /packages/joopjoop-core && pip install -e .

# API 서비스 의존성 파일 복사
COPY services/backend/pyproject.toml services/backend/poetry.lock ./

# poetry.toml 설정 파일 생성
RUN echo '[virtualenvs]\ncreate = false\nin-project = false' > poetry.toml

# 의존성 설치 (joopjoop-core는 이미 pip로 설치되어 있으므로 무시)
RUN poetry config repositories.joopjoop-core /packages/joopjoop-core && \
    poetry install --no-root --no-interaction --no-ansi

# Final stage
FROM python:3.11-slim

WORKDIR /app

# 필요한 시스템 패키지만 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Builder stage에서 설치된 Python 패키지들을 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# joopjoop-core 소스 코드 복사
COPY packages/joopjoop-core/src /packages/joopjoop-core/src

# API 서비스 소스 코드 복사
COPY services/backend/app ./app

# Python 패키지 경로 설정
ENV PYTHONPATH=/app:/packages/joopjoop-core/src

# 실행
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

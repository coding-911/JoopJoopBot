FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install --no-cache-dir poetry

# joopjoop-core 패키지 복사 및 설치
COPY packages/joopjoop-core /packages/joopjoop-core
RUN pip install -e /packages/joopjoop-core

# API 서비스 의존성 파일 복사
COPY services/api/pyproject.toml services/api/poetry.lock ./

# 의존성 설치
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# 소스 코드 복사
COPY services/api/src ./src

# 실행
CMD ["poetry", "run", "uvicorn", "src.joopjoop_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 
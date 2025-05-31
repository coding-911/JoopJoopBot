FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install --no-cache-dir poetry

# 깨진 virtualenv 제거 (중요!)
RUN rm -rf /app/.venv

# joopjoop-core 패키지 복사 및 설치
COPY packages/joopjoop-core /packages/joopjoop-core
RUN cd /packages/joopjoop-core && pip install -e .

# API 서비스 의존성 파일 복사
COPY services/backend/pyproject.toml services/backend/poetry.lock ./

# 의존성 설치
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# 소스 코드 복사
COPY services/backend/app ./app

# Python 패키지 경로 설정
ENV PYTHONPATH=/app:/packages/joopjoop-core/src

# 실행
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 
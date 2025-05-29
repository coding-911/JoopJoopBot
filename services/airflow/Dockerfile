FROM apache/airflow:2.7.1-python3.11

USER root

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# 추가 의존성 설치
COPY services/airflow/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# joopjoop-core 패키지 설치
COPY packages/joopjoop-core /packages/joopjoop-core
RUN pip install -e /packages/joopjoop-core 
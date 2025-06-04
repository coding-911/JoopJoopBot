# Builder stage
FROM apache/airflow:2.7.1-python3.11 as builder

USER root

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# joopjoop-core 패키지 복사
COPY packages/joopjoop-core /packages/joopjoop-core

# 파일 복사 확인 및 권한 설정
RUN echo "=== Setting permissions ===" && \
    chown -R airflow:0 /packages/joopjoop-core && \
    chmod -R g+rw /packages/joopjoop-core && \
    find /packages/joopjoop-core -type d -exec chmod 755 {} \;

# Final stage
FROM apache/airflow:2.7.1-python3.11

USER root

# 필요한 시스템 패키지만 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# joopjoop-core 소스 코드 복사
COPY packages/joopjoop-core /packages/joopjoop-core
COPY services/airflow/requirements.txt /requirements.txt

USER airflow

WORKDIR /opt/airflow

# 패키지 설치를 airflow 유저 환경에서 직접 실행
RUN pip install --default-timeout=120 --retries=10 --no-cache-dir -r /requirements.txt
RUN pip install --default-timeout=120 --retries=10 --no-cache-dir -e /packages/joopjoop-core

# DAGs 복사 및 권한 설정
COPY --chown=airflow:root services/airflow/dags /opt/airflow/dags
RUN chmod -R 644 /opt/airflow/dags/*.py

# Python 패키지 경로 설정
ENV PYTHONPATH=/opt/airflow:/packages/joopjoop-core/src

#!/bin/bash

set -e
set -u

# Load environment variables from .env file
if [ -f "/.env" ]; then
    export $(cat /.env | grep -v '^#' | xargs)
elif [ -f "/docker-entrypoint-initdb.d/.env" ]; then
    export $(cat /docker-entrypoint-initdb.d/.env | grep -v '^#' | xargs)
fi

function create_user_and_database() {
    local database=$1
    echo "  Creating database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $database;
EOSQL
}

# Print current configuration
echo "Current configuration:"
echo "POSTGRES_MULTIPLE_DATABASES: $POSTGRES_MULTIPLE_DATABASES"
echo "AIRFLOW_POSTGRES_USER: $AIRFLOW_POSTGRES_USER"
echo "AIRFLOW_POSTGRES_DB: $AIRFLOW_POSTGRES_DB"
echo "TEST_POSTGRES_USER: $TEST_POSTGRES_USER"

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        # Skip if it's the default database
        if [ "$db" != "$POSTGRES_DB" ]; then
            create_user_and_database $db
        fi
    done
    
    # Create Airflow user and grant privileges
    echo "Creating Airflow user"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE USER $AIRFLOW_POSTGRES_USER WITH PASSWORD '$AIRFLOW_POSTGRES_PASSWORD';
        GRANT ALL PRIVILEGES ON DATABASE $AIRFLOW_POSTGRES_DB TO $AIRFLOW_POSTGRES_USER;
EOSQL

    # Create Test user and grant privileges
    echo "Creating Test user"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE USER $TEST_POSTGRES_USER WITH PASSWORD '$TEST_POSTGRES_PASSWORD';
        GRANT ALL PRIVILEGES ON DATABASE $TEST_API_POSTGRES_DB TO $TEST_POSTGRES_USER;
        GRANT ALL PRIVILEGES ON DATABASE $TEST_AIRFLOW_POSTGRES_DB TO $TEST_POSTGRES_USER;
        
        -- API 테스트 DB 권한 설정
        \c $TEST_API_POSTGRES_DB;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $TEST_POSTGRES_USER;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $TEST_POSTGRES_USER;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $TEST_POSTGRES_USER;
        GRANT ALL PRIVILEGES ON SCHEMA public TO $TEST_POSTGRES_USER;
        
        -- Airflow 테스트 DB 권한 설정
        \c $TEST_AIRFLOW_POSTGRES_DB;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $TEST_POSTGRES_USER;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $TEST_POSTGRES_USER;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $TEST_POSTGRES_USER;
        GRANT ALL PRIVILEGES ON SCHEMA public TO $TEST_POSTGRES_USER;
EOSQL
    
    echo "Multiple databases and users created"
fi
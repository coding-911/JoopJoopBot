import os
import tempfile
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from joopjoop.models import Base

def find_project_root() -> Path:
    """프로젝트 루트 디렉토리 찾기"""
    current = Path(__file__).resolve().parent
    while current.name != "JoopJoopBot" and current.parent != current:
        current = current.parent
    return current

@pytest.fixture(scope="session")
def project_root():
    """프로젝트 루트 경로"""
    return find_project_root()

@pytest.fixture(scope="session")
def pg_test_config():
    """PostgreSQL 테스트 DB 설정"""
    return {
        'host': 'localhost',  # Docker 외부에서 실행할 때는 항상 localhost 사용
        'port': int(os.getenv('POSTGRES_PORT', '15432')),
        'dbname': os.getenv('TEST_AIRFLOW_POSTGRES_DB', 'api_test'),
        'user': os.getenv('TEST_POSTGRES_USER', 'test'),
        'password': os.getenv('TEST_POSTGRES_PASSWORD', '1234')
    }

@pytest.fixture(scope="session")
def pg_test_airflow_config():
    """Airflow 테스트용 PostgreSQL DB 설정"""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '15432')),
        'dbname': os.getenv('TEST_AIRFLOW_POSTGRES_DB', 'airflow_test'),  # Airflow 테스트용 DB
        'user': os.getenv('TEST_POSTGRES_USER', 'test'),
        'password': os.getenv('TEST_POSTGRES_PASSWORD', '1234')
    }

@pytest.fixture(scope="session")
def temp_db_path():
    """임시 DB 파일 경로 생성 (SQLAlchemy 테스트용)"""
    temp_dir = tempfile.mkdtemp(prefix="test_")
    db_path = Path(temp_dir) / "test.db"
    yield str(db_path)
    
    # 테스트 종료 후 정리
    try:
        if db_path.exists():
            db_path.unlink()
        os.rmdir(temp_dir)
        print(f"\n임시 DB 파일 삭제 완료: {temp_dir}")
    except Exception as e:
        print(f"\n임시 DB 파일 삭제 실패: {str(e)}")

@pytest.fixture(scope="session")
def temp_db_url(temp_db_path):
    """임시 DB URL 생성 (SQLAlchemy 테스트용)"""
    return f"sqlite:///{temp_db_path}"

@pytest.fixture(scope="session")
def temp_db_engine(temp_db_url):
    """임시 DB 엔진 생성 (SQLAlchemy 테스트용)"""
    engine = create_engine(temp_db_url)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def temp_db_session(temp_db_engine):
    """임시 DB 세션 생성 (SQLAlchemy 테스트용)"""
    SessionLocal = sessionmaker(bind=temp_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="session")
def temp_vector_store_path():
    """임시 벡터 저장소 경로 생성"""
    temp_dir = tempfile.mkdtemp(prefix="vector_test_")
    yield temp_dir
    
    # 테스트 종료 후 정리
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n임시 벡터 저장소 삭제 완료: {temp_dir}")
    except Exception as e:
        print(f"\n임시 벡터 저장소 삭제 실패: {str(e)}")

@pytest.fixture(scope="session")
def dart_api_key(project_root):
    """DART API 키"""
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
    
    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        raise ValueError(
            "DART_API_KEY 환경변수가 설정되지 않았습니다.\n"
            f"프로젝트 루트({project_root})의 .env 파일을 확인해주세요."
        )
    return api_key 
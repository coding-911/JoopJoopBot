import os
import pytest
from pathlib import Path

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
def temp_vector_store_path():
    """임시 벡터 저장소 경로 생성"""
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="airflow_vector_test_")
    yield temp_dir
    
    # 테스트 종료 후 정리
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n임시 벡터 저장소 삭제 완료: {temp_dir}")
    except Exception as e:
        print(f"\n임시 벡터 저장소 삭제 실패: {str(e)}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_env(project_root):
    """테스트 환경변수 설정"""
    # 기존 환경변수 백업
    orig_db = os.environ.get('POSTGRES_DB')
    orig_user = os.environ.get('POSTGRES_USER')
    orig_password = os.environ.get('POSTGRES_PASSWORD')
    
    # 테스트용 환경변수 설정
    os.environ['POSTGRES_DB'] = os.getenv('TEST_AIRFLOW_POSTGRES_DB', 'airflow_test')
    os.environ['POSTGRES_USER'] = os.getenv('TEST_POSTGRES_USER', 'test')
    os.environ['POSTGRES_PASSWORD'] = os.getenv('TEST_POSTGRES_PASSWORD', '1234')
    os.environ['VECTOR_DB_PATH'] = os.getenv('AIRFLOW_VECTOR_DB_PATH', '/opt/airflow/vector_store')
    
    yield
    
    # 원래 환경변수 복원
    if orig_db:
        os.environ['POSTGRES_DB'] = orig_db
    if orig_user:
        os.environ['POSTGRES_USER'] = orig_user
    if orig_password:
        os.environ['POSTGRES_PASSWORD'] = orig_password 
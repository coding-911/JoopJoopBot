import os
import tempfile
import pytest
from pathlib import Path
import psycopg2
from psycopg2.extras import DictCursor

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
def temp_db_config():
    """PostgreSQL 테스트 DB 설정"""
    return {
        'host': 'localhost',  # Docker 외부에서 실행할 때는 항상 localhost 사용
        'port': int(os.getenv('POSTGRES_PORT', '15432')),
        'dbname': os.getenv('TEST_POSTGRES_DB', 'api_test'),
        'user': os.getenv('TEST_POSTGRES_USER', 'test'),
        'password': os.getenv('TEST_POSTGRES_PASSWORD', '1234')
    }

@pytest.fixture(scope="function")
def temp_db_connection(temp_db_config):
    """PostgreSQL 테스트 DB 연결"""
    conn = psycopg2.connect(**temp_db_config, cursor_factory=DictCursor)
    try:
        # 테이블 생성
        with conn.cursor() as cur:
            # DART 보고서 테이블
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dart_reports (
                    id SERIAL PRIMARY KEY,
                    corp_code VARCHAR(8) NOT NULL,
                    corp_name VARCHAR(100) NOT NULL,
                    receipt_no VARCHAR(14) NOT NULL UNIQUE,
                    report_type VARCHAR(100) NOT NULL,
                    title VARCHAR(300) NOT NULL,
                    content TEXT NOT NULL,
                    disclosure_date DATE NOT NULL,
                    meta_data JSONB
                );
                CREATE INDEX IF NOT EXISTS idx_dart_reports_corp_code ON dart_reports(corp_code);
                CREATE INDEX IF NOT EXISTS idx_dart_reports_receipt_no ON dart_reports(receipt_no);
                CREATE INDEX IF NOT EXISTS idx_dart_reports_disclosure_date ON dart_reports(disclosure_date);
            """)
            
            # 기업 정보 테이블
            cur.execute("""
                CREATE TABLE IF NOT EXISTS corps (
                    id SERIAL PRIMARY KEY,
                    corp_code VARCHAR(8) NOT NULL UNIQUE,
                    corp_name VARCHAR(100) NOT NULL,
                    stock_code VARCHAR(6),
                    is_listed BOOLEAN DEFAULT FALSE,
                    last_collection_at TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_corps_corp_code ON corps(corp_code);
                CREATE INDEX IF NOT EXISTS idx_corps_stock_code ON corps(stock_code);
            """)
            conn.commit()
        
        yield conn
    finally:
        # 테이블 삭제
        with conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS dart_reports;
                DROP TABLE IF EXISTS corps;
            """)
            conn.commit()
        conn.close()

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
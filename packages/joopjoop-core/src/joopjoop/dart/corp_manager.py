from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CorpManager:
    """기업 정보 관리 클래스"""
    
    def __init__(self, db_config: Dict):
        """
        Args:
            db_config: PostgreSQL 연결 설정
                {
                    'host': str,
                    'dbname': str,
                    'user': str,
                    'password': str,
                    'port': int
                }
        """
        self.db_config = db_config
        self._init_db()
    
    def _init_db(self):
        """DB 초기화"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                # 기업 정보 테이블 생성
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
    
    def upsert_corps(self, corps: List[Dict]) -> None:
        """
        기업 정보 업데이트 또는 삽입
        
        Args:
            corps: 기업 정보 목록
                [
                    {
                        'corp_code': str,  # 기업 고유번호
                        'corp_name': str,  # 기업명
                        'stock_code': str,  # 주식코드 (선택)
                    },
                    ...
                ]
        """
        now = datetime.now()
        
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                for corp in corps:
                    cur.execute("""
                        INSERT INTO corps (
                            corp_code, corp_name, stock_code, is_listed, last_collection_at
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (corp_code) DO UPDATE SET
                            corp_name = EXCLUDED.corp_name,
                            stock_code = EXCLUDED.stock_code,
                            is_listed = EXCLUDED.is_listed,
                            last_collection_at = EXCLUDED.last_collection_at
                    """, (
                        corp['corp_code'],
                        corp['corp_name'],
                        corp.get('stock_code'),
                        bool(corp.get('stock_code')),  # 주식코드가 있으면 상장기업
                        now
                    ))
                conn.commit()
    
    def update_collection_timestamp(self, corp_code: str) -> None:
        """
        수집 완료 시간 업데이트
        
        Args:
            corp_code: 기업 고유번호
        """
        now = datetime.now()
        
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE corps 
                    SET last_collection_at = %s
                    WHERE corp_code = %s
                """, (now, corp_code))
                conn.commit()
    
    def get_all_corps(self, only_listed: bool = False) -> List[Dict]:
        """
        전체 기업 목록 조회
        
        Args:
            only_listed: 상장기업만 조회할지 여부
            
        Returns:
            List[Dict]: 기업 목록
        """
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                if only_listed:
                    cur.execute("""
                        SELECT * FROM corps 
                        WHERE is_listed = TRUE 
                        ORDER BY corp_name
                    """)
                else:
                    cur.execute("SELECT * FROM corps ORDER BY corp_name")
                
                return [dict(row) for row in cur.fetchall()]
    
    def get_corp(self, corp_code: str) -> Optional[Dict]:
        """
        기업 정보 조회
        
        Args:
            corp_code: 기업 고유번호
            
        Returns:
            Optional[Dict]: 기업 정보
        """
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM corps 
                    WHERE corp_code = %s
                """, (corp_code,))
                row = cur.fetchone()
                return dict(row) if row else None 
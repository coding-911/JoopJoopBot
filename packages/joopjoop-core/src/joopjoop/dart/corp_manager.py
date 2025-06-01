from typing import List, Dict, Optional, Union
import psycopg2
import sqlite3
from psycopg2.extras import DictCursor
from datetime import datetime
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class CorpManager:
    """기업 정보 관리 클래스"""
    
    def __init__(self, db_url: Union[str, Dict]):
        """
        Args:
            db_url: DB 연결 정보
                - PostgreSQL: Dict 형태의 연결 설정
                    {
                        'host': str,
                        'dbname': str,
                        'user': str,
                        'password': str,
                        'port': int
                    }
                - SQLite: 'sqlite:///path/to/db.sqlite' 형태의 URL
        """
        self.db_url = db_url
        self._init_db()
    
    def _get_connection(self):
        """DB 연결 생성"""
        if isinstance(self.db_url, dict):
            # PostgreSQL
            return psycopg2.connect(**self.db_url)
        else:
            # SQLite
            if isinstance(self.db_url, str):
                if self.db_url.startswith('sqlite:///'):
                    db_path = self.db_url[10:]  # Remove 'sqlite:///'
                else:
                    db_path = self.db_url
                return sqlite3.connect(db_path)
            else:
                raise ValueError("Invalid db_url format")
    
    def _init_db(self):
        """DB 테이블 초기화"""
        is_sqlite = isinstance(self.db_url, str)
        
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS corps (
                corp_code VARCHAR(8) PRIMARY KEY,
                corp_name VARCHAR(100) NOT NULL,
                stock_code VARCHAR(6),
                is_listed BOOLEAN,
                modified_at TIMESTAMP{tz},
                last_update TIMESTAMP{tz}
            )
        """.format(tz="" if is_sqlite else " WITH TIME ZONE")
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            conn.commit()
    
    def upsert_corps(self, corps: List[Dict]) -> None:
        """
        기업 정보 업데이트 또는 삽입
        
        Args:
            corps: 기업 정보 목록 [{'corp_code': str, 'corp_name': str, 'stock_code': str}, ...]
        """
        now = datetime.now()
        is_sqlite = isinstance(self.db_url, str)
        
        if is_sqlite:
            upsert_sql = """
                INSERT OR REPLACE INTO corps (
                    corp_code, corp_name, stock_code, 
                    is_listed, modified_at
                )
                VALUES (?, ?, ?, ?, ?)
            """
        else:
            upsert_sql = """
                INSERT INTO corps (
                    corp_code, corp_name, stock_code, 
                    is_listed, modified_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (corp_code) DO UPDATE SET
                    corp_name = EXCLUDED.corp_name,
                    stock_code = EXCLUDED.stock_code,
                    is_listed = EXCLUDED.is_listed,
                    modified_at = EXCLUDED.modified_at
            """
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                for corp in corps:
                    cur.execute(upsert_sql, (
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
        is_sqlite = isinstance(self.db_url, str)
        param_style = '?' if is_sqlite else '%s'
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE corps 
                    SET last_update = {param_style}
                    WHERE corp_code = {param_style}
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
        with self._get_connection() as conn:
            if isinstance(self.db_url, str):
                # SQLite
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
            else:
                # PostgreSQL
                cur = conn.cursor(cursor_factory=DictCursor)
            
            query = "SELECT * FROM corps"
            if only_listed:
                query += " WHERE is_listed = true"
            query += " ORDER BY last_update ASC NULLS FIRST"
            
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()] 
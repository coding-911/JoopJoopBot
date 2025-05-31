from typing import List, Dict, Optional
import sqlite3
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CorpManager:
    """기업 정보 관리 클래스"""
    
    def __init__(self, db_path: str):
        """
        Args:
            db_path: SQLite DB 파일 경로
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """DB 테이블 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS corps (
                    corp_code TEXT PRIMARY KEY,
                    corp_name TEXT NOT NULL,
                    stock_code TEXT,
                    is_listed BOOLEAN,
                    modified_at TIMESTAMP,
                    last_update TIMESTAMP
                )
            """)
            conn.commit()
    
    def upsert_corps(self, corps: List[Dict]) -> None:
        """
        기업 정보 업데이트 또는 삽입
        
        Args:
            corps: 기업 정보 목록 [{'corp_code': str, 'corp_name': str, 'stock_code': str}, ...]
        """
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for corp in corps:
                conn.execute("""
                    INSERT INTO corps (
                        corp_code, corp_name, stock_code, 
                        is_listed, modified_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(corp_code) DO UPDATE SET
                        corp_name = excluded.corp_name,
                        stock_code = excluded.stock_code,
                        is_listed = excluded.is_listed,
                        modified_at = excluded.modified_at
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
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE corps 
                SET last_update = ?
                WHERE corp_code = ?
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
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM corps"
            if only_listed:
                query += " WHERE is_listed = 1"
            query += " ORDER BY last_update ASC NULLS FIRST"
            
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()] 
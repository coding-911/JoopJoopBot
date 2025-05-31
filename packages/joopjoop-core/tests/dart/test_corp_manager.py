import os
import tempfile
import sqlite3
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from joopjoop.dart import DartClient, CorpManager

# 프로젝트 루트 디렉토리 찾기
def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current.name != "JoopJoopBot" and current.parent != current:
        current = current.parent
    return current

# 환경변수 로드
project_root = find_project_root()
load_dotenv(project_root / ".env")

class TestCorpManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 환경 설정"""
        # 임시 DB 파일 생성
        self.temp_dir = tempfile.mkdtemp(prefix="corp_manager_test_")
        self.db_path = Path(self.temp_dir) / "test.db"
        
        # DART API 키 설정
        self.api_key = os.getenv("DART_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DART_API_KEY 환경변수가 설정되지 않았습니다.\n"
                f"프로젝트 루트({project_root})의 .env 파일을 확인해주세요."
            )
        
        # CorpManager 및 DartClient 초기화
        self.client = DartClient(self.api_key)
        self.manager = CorpManager(str(self.db_path))
        
        yield
        
        # 테스트 종료 후 정리
        try:
            if self.db_path.exists():
                self.db_path.unlink()
            os.rmdir(self.temp_dir)
            print(f"\n임시 DB 파일 삭제 완료: {self.temp_dir}")
        except Exception as e:
            print(f"\n임시 DB 파일 삭제 실패: {str(e)}")
    
    async def test_db_initialization(self):
        """DB 초기화 테스트"""
        # DB 파일이 생성되었는지 확인
        assert self.db_path.exists()
        
        # 테이블이 생성되었는지 확인
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # corps 테이블 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='corps'
            """)
            assert cursor.fetchone() is not None
            
            # 테이블 스키마 확인
            cursor.execute("PRAGMA table_info(corps)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                'corp_code', 'corp_name', 'stock_code', 
                'is_listed', 'last_updated'
            }
            assert required_columns.issubset(columns)
    
    async def test_update_corps(self):
        """기업 정보 업데이트 테스트"""
        # 1. DART API로 기업 목록 조회
        corps = await self.client.get_corp_codes()
        assert len(corps) > 0
        
        # 2. 기업 정보 업데이트
        updated_count = await self.manager.update_corps(corps)
        assert updated_count > 0
        
        # 3. DB에 저장된 기업 수 확인
        stored_corps = self.manager.get_all_corps()
        assert len(stored_corps) == len(corps)
        
        # 4. 샘플 기업 정보 확인
        samsung = self.manager.get_corp_by_code("00126380")  # 삼성전자
        assert samsung is not None
        assert samsung['corp_name'] == "삼성전자"
        assert samsung['stock_code'] is not None
        assert samsung['is_listed'] is True
    
    def test_get_listed_corps(self):
        """상장기업 조회 테스트"""
        # 1. 테스트용 기업 데이터 추가
        test_corps = [
            {
                'corp_code': '00126380',
                'corp_name': '삼성전자',
                'stock_code': '005930',
                'is_listed': True,
                'last_updated': datetime.now().isoformat()
            },
            {
                'corp_code': '00000001',
                'corp_name': '비상장테스트',
                'stock_code': None,
                'is_listed': False,
                'last_updated': datetime.now().isoformat()
            }
        ]
        
        for corp in test_corps:
            self.manager.add_corp(corp)
        
        # 2. 상장기업만 조회
        listed_corps = self.manager.get_listed_corps()
        assert len(listed_corps) == 1
        assert listed_corps[0]['corp_code'] == '00126380'
        assert listed_corps[0]['is_listed'] is True
    
    def test_corp_crud_operations(self):
        """기업 정보 CRUD 테스트"""
        # 1. Create
        corp_data = {
            'corp_code': 'TEST001',
            'corp_name': '테스트기업',
            'stock_code': '999999',
            'is_listed': True,
            'last_updated': datetime.now().isoformat()
        }
        self.manager.add_corp(corp_data)
        
        # 2. Read
        corp = self.manager.get_corp_by_code('TEST001')
        assert corp is not None
        assert corp['corp_name'] == '테스트기업'
        
        # 3. Update
        corp_data['corp_name'] = '테스트기업_수정'
        self.manager.update_corp(corp_data)
        updated_corp = self.manager.get_corp_by_code('TEST001')
        assert updated_corp['corp_name'] == '테스트기업_수정'
        
        # 4. Delete
        self.manager.delete_corp('TEST001')
        deleted_corp = self.manager.get_corp_by_code('TEST001')
        assert deleted_corp is None
    
    def test_last_updated_tracking(self):
        """마지막 수집 시간 추적 테스트"""
        # 1. 기업 추가
        corp_data = {
            'corp_code': 'TEST001',
            'corp_name': '테스트기업',
            'stock_code': '999999',
            'is_listed': True,
            'last_updated': '2024-01-01T00:00:00'
        }
        self.manager.add_corp(corp_data)
        
        # 2. 초기 last_updated 확인
        corp = self.manager.get_corp_by_code('TEST001')
        assert corp['last_updated'] == '2024-01-01T00:00:00'
        
        # 3. 업데이트 수행
        corp_data['last_updated'] = '2024-01-02T00:00:00'
        self.manager.update_corp(corp_data)
        
        # 4. 업데이트된 last_updated 확인
        updated_corp = self.manager.get_corp_by_code('TEST001')
        assert updated_corp['last_updated'] == '2024-01-02T00:00:00' 
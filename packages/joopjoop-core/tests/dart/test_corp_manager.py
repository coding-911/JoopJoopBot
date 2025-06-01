import pytest
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
from joopjoop.dart import DartClient, CorpManager

@pytest.mark.integration
class TestCorpManager:
    @pytest.fixture(autouse=True)
    def setup(self, pg_test_config, dart_api_key):
        """테스트 환경 설정"""
        self.client = DartClient(dart_api_key)
        self.manager = CorpManager(pg_test_config)
        
        yield
        
        # 테스트 후 정리
        with psycopg2.connect(**pg_test_config) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS corps")
                conn.commit()
    
    @pytest.mark.asyncio
    async def test_db_initialization(self):
        """DB 초기화 테스트"""
        with psycopg2.connect(**self.manager.db_url) as conn:
            with conn.cursor() as cur:
                # corps 테이블 확인
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'corps'
                """)
                assert cur.fetchone() is not None
                
                # 테이블 스키마 확인
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'corps'
                """)
                columns = {row[0] for row in cur.fetchall()}
                required_columns = {
                    'corp_code', 'corp_name', 'stock_code', 
                    'is_listed', 'last_update', 'modified_at'
                }
                assert required_columns.issubset(columns)
    
    @pytest.mark.asyncio
    async def test_update_corps(self):
        """기업 정보 업데이트 테스트"""
        # 1. DART API로 기업 목록 조회
        corps = await self.client.get_corp_codes()
        assert len(corps) > 0
        
        # 2. 기업 정보 업데이트
        self.manager.upsert_corps(corps)
        
        # 3. DB에 저장된 기업 수 확인
        stored_corps = self.manager.get_all_corps()
        assert len(stored_corps) == len(corps)
        
        # 4. 샘플 기업 정보 확인
        samsung = next(
            (corp for corp in stored_corps if corp['corp_code'] == "00126380"),
            None
        )
        assert samsung is not None
        assert samsung['corp_name'] == "삼성전자"
        assert samsung['stock_code'] is not None
        assert samsung['is_listed'] is True
        assert samsung['modified_at'] is not None
    
    def test_get_listed_corps(self):
        """상장기업 조회 테스트"""
        # 1. 테스트용 기업 데이터 추가
        test_corps = [
            {
                'corp_code': '00126380',
                'corp_name': '삼성전자',
                'stock_code': '005930',
                'is_listed': True,
                'modified_at': datetime.now()
            },
            {
                'corp_code': '00000001',
                'corp_name': '비상장테스트',
                'stock_code': None,
                'is_listed': False,
                'modified_at': datetime.now()
            }
        ]
        
        self.manager.upsert_corps(test_corps)
        
        # 2. 상장기업만 조회
        listed_corps = self.manager.get_all_corps(only_listed=True)
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
            'modified_at': datetime.now()
        }
        self.manager.upsert_corps([corp_data])
        
        # 2. Read
        stored_corps = self.manager.get_all_corps()
        corp = next(
            (corp for corp in stored_corps if corp['corp_code'] == 'TEST001'),
            None
        )
        assert corp is not None
        assert corp['corp_name'] == '테스트기업'
        
        # 3. Update
        corp_data['corp_name'] = '테스트기업_수정'
        self.manager.upsert_corps([corp_data])
        
        stored_corps = self.manager.get_all_corps()
        updated_corp = next(
            (corp for corp in stored_corps if corp['corp_code'] == 'TEST001'),
            None
        )
        assert updated_corp['corp_name'] == '테스트기업_수정'
    
    def test_last_updated_tracking(self):
        """마지막 수집 시간 추적 테스트"""
        # 1. 기업 추가
        corp_data = {
            'corp_code': 'TEST001',
            'corp_name': '테스트기업',
            'stock_code': '999999',
            'is_listed': True,
            'modified_at': datetime.now()
        }
        self.manager.upsert_corps([corp_data])
        
        # 2. 수집 시간 업데이트
        self.manager.update_collection_timestamp('TEST001')
        
        # 3. 업데이트된 시간 확인
        stored_corps = self.manager.get_all_corps()
        updated_corp = next(
            (corp for corp in stored_corps if corp['corp_code'] == 'TEST001'),
            None
        )
        assert updated_corp is not None
        assert updated_corp['last_update'] is not None 
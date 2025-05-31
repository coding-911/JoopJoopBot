from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta

from joopjoop.dart import DartClient
from joopjoop.rag import RAGPipeline

router = APIRouter(prefix="/dart", tags=["dart"])

# 환경변수에서 API 키 가져오기
DART_API_KEY = os.getenv("DART_API_KEY")
if not DART_API_KEY:
    raise ValueError("DART_API_KEY 환경변수가 설정되지 않았습니다.")

# 벡터 스토어 경로 설정
DEFAULT_VECTOR_STORE_PATH = os.getenv("VECTOR_DB_PATH", "/app/data/vector_store")

# DART 클라이언트 초기화
dart_client = DartClient(DART_API_KEY)

@router.get("/corps", response_model=List[Dict])
async def get_corps():
    """기업 목록 조회 테스트"""
    try:
        return await dart_client.get_corp_codes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기업 목록 조회 실패: {str(e)}")

@router.get("/company/{corp_code}", response_model=Dict)
async def get_company_info(corp_code: str):
    """기업 기본정보 조회 테스트"""
    try:
        return await dart_client.get_company_info(corp_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기업 정보 조회 실패: {str(e)}")

@router.get("/disclosures/{corp_code}", response_model=List[Dict])
async def get_disclosures(
    corp_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """공시 목록 조회 테스트"""
    try:
        return await dart_client.get_disclosure_list(corp_code, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"공시 목록 조회 실패: {str(e)}")

@router.get("/document/{rcp_no}", response_model=Dict)
async def get_document(rcp_no: str):
    """공시 원문 조회 테스트"""
    try:
        return await dart_client.get_document(rcp_no)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"공시 원문 조회 실패: {str(e)}")

@router.post("/collect/{corp_code}")
async def collect_and_store(
    corp_code: str,
    days: int = 7,
    vector_store_path: str = DEFAULT_VECTOR_STORE_PATH
):
    """특정 기업의 공시 데이터 수집 및 벡터 DB 저장 테스트"""
    try:
        # 공시 목록 조회
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        end_date = datetime.now().strftime('%Y%m%d')
        
        disclosures = await dart_client.get_disclosure_list(
            corp_code=corp_code,
            start_date=start_date,
            end_date=end_date
        )
        
        # 공시 원문 조회 및 벡터 DB 저장
        pipeline = RAGPipeline(vector_store_path)
        processed_count = 0
        
        for disc in disclosures:
            document = await dart_client.get_document(disc['rcept_no'])
            if document:
                pipeline.process_document(document)
                processed_count += 1
        
        return {
            "status": "success",
            "message": f"{processed_count}개의 공시가 처리되었습니다.",
            "corp_code": corp_code,
            "period": f"{start_date} ~ {end_date}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터 수집 및 저장 실패: {str(e)}"
        ) 
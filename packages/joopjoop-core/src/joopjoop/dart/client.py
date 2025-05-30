import os
import json
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import pandas as pd
from typing import List, Dict, Optional
import logging
import zipfile
from io import BytesIO
import warnings

# XML 파싱 경고 무시
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logger = logging.getLogger(__name__)

class DartClient:
    """DART API 클라이언트"""
    
    BASE_URL = "https://opendart.fss.or.kr/api"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        DART OpenAPI 클라이언트 초기화
        
        Args:
            api_key: DART OpenAPI 인증키. 없으면 환경변수 DART_API_KEY 사용
        """
        self.api_key = api_key or os.getenv("DART_API_KEY")
        if not self.api_key:
            raise ValueError("DART API 키가 설정되지 않았습니다.")
        logger.debug("DartClient 초기화 완료")
        
    async def get_corp_codes(self) -> List[Dict]:
        """
        기업 고유번호 목록 조회
        
        Returns:
            List[Dict]: 기업 목록. 각 기업은 corp_code(고유번호)와 corp_name(회사명) 포함
        """
        url = f"{self.BASE_URL}/corpCode.xml"
        params = {"crtfc_key": self.api_key}
        
        try:
            logger.debug(f"기업 목록 API 호출: {url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                logger.debug(f"API 응답 상태 코드: {response.status_code}")
                logger.debug(f"API 응답 내용: {response.text[:200]}...")  # 처음 200자만 로깅
                
                if response.status_code != 200:
                    logger.error(f"API 오류 응답: {response.text}")
                    return []
                
                # ZIP 파일 처리
                zip_data = BytesIO(response.content)
                with zipfile.ZipFile(zip_data) as zip_file:
                    # CORPCODE.xml 파일 찾기
                    xml_filename = next((name for name in zip_file.namelist() if name.lower() == 'corpcode.xml'), None)
                    if not xml_filename:
                        logger.error("ZIP 파일에서 CORPCODE.xml을 찾을 수 없습니다.")
                        return []
                    
                    # XML 파일 읽기
                    with zip_file.open(xml_filename) as xml_file:
                        xml_content = xml_file.read()
                        logger.debug(f"XML 파일 내용 (처음 200바이트): {xml_content[:200]}")
                
                # XML 파싱
                soup = BeautifulSoup(xml_content, 'lxml')
                corps = []
                
                for corp in soup.find_all('list'):
                    corps.append({
                        'corp_code': corp.find('corp_code').text.strip(),
                        'corp_name': corp.find('corp_name').text.strip(),
                        'stock_code': corp.find('stock_code').text.strip(),
                        'modify_date': corp.find('modify_date').text.strip()
                    })
                
                logger.debug(f"파싱된 기업 수: {len(corps)}")
                return corps
                
        except Exception as e:
            logger.error(f"API 호출 중 예외 발생: {str(e)}", exc_info=True)
            return []
            
    async def get_company_info(self, corp_code: str) -> Dict:
        """기업 기본정보 조회"""
        url = f"{self.BASE_URL}/company.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json()
            
    async def get_disclosure_list(
        self,
        corp_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """공시 목록 조회"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
            
        url = f"{self.BASE_URL}/list.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bgn_de": start_date,
            "end_de": end_date,
            "page_count": 100
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            return data.get('list', [])
            
    async def get_document(self, rcp_no: str) -> Dict:
        """
        공시 원문 조회
        
        Args:
            rcp_no: 접수번호
            
        Returns:
            Dict: 공시 문서 정보 (제목, 본문, 접수번호, 공시일자 등)
        """
        url = f"{self.BASE_URL}/document.xml"
        params = {
            "crtfc_key": self.api_key,
            "rcept_no": rcp_no
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.error(f"문서 조회 실패 (상태 코드: {response.status_code})")
                    return {}
                
                # ZIP 파일 처리
                zip_data = BytesIO(response.content)
                with zipfile.ZipFile(zip_data) as zip_file:
                    # 첫 번째 XML 파일 찾기 (일반적으로 접수번호.xml)
                    xml_files = [f for f in zip_file.namelist() if f.lower().endswith('.xml')]
                    if not xml_files:
                        logger.error("ZIP 파일에서 XML 문서를 찾을 수 없습니다.")
                        return {}
                    
                    # XML 파일 읽기
                    with zip_file.open(xml_files[0]) as xml_file:
                        xml_content = xml_file.read()
                        soup = BeautifulSoup(xml_content, 'lxml')
                        
                        # dcm_no: 문서 번호
                        dcm_no = soup.find('dcm_no')
                        # report_nm: 보고서 이름
                        report_nm = soup.find('report_nm')
                        # corp_cls: 법인구분
                        corp_cls = soup.find('corp_cls')
                        # corp_name: 법인명
                        corp_name = soup.find('corp_name')
                        # content: 공시 본문 (모든 텍스트)
                        content = soup.get_text(strip=True)
                        
                        return {
                            'title': report_nm.text if report_nm else '',
                            'corp_name': corp_name.text if corp_name else '',
                            'corp_cls': corp_cls.text if corp_cls else '',
                            'dcm_no': dcm_no.text if dcm_no else '',
                            'content': content,
                            'receipt_no': rcp_no
                        }
                        
        except Exception as e:
            logger.error(f"문서 조회 중 오류 발생: {str(e)}", exc_info=True)
            return {}

    def parse_xml_content(self, xml_content: bytes) -> BeautifulSoup:
        """XML 내용을 파싱"""
        return BeautifulSoup(xml_content, 'lxml-xml')  # lxml-xml 파서 사용 
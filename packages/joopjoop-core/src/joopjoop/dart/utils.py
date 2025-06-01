from datetime import datetime
from typing import Optional

def parse_date(date_str: str) -> datetime:
    """
    다양한 형식의 날짜 문자열을 datetime 객체로 변환
    
    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD 또는 YYYYMMDD 형식)
        
    Returns:
        datetime: 변환된 datetime 객체
    """
    if "-" in date_str:
        return datetime.strptime(date_str, "%Y-%m-%d")
    else:
        return datetime.strptime(date_str, "%Y%m%d")

def format_date_for_db(date: datetime) -> str:
    """
    datetime 객체를 DB 저장용 문자열로 변환 (YYYY-MM-DD)
    """
    return date.strftime("%Y-%m-%d")

def format_date_for_api(date: datetime) -> str:
    """
    datetime 객체를 API 요청용 문자열로 변환 (YYYYMMDD)
    """
    return date.strftime("%Y%m%d") 
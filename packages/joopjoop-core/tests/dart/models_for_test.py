from datetime import date
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, Date, JSON, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DartReport(Base):
    """DART 공시 보고서 (테스트용)"""
    __tablename__ = "dart_reports"

    id = Column(Integer, primary_key=True, index=True)
    corp_code = Column(String(8), nullable=False, index=True)
    corp_name = Column(String(100), nullable=False)
    receipt_no = Column(String(14), nullable=False, unique=True, index=True)
    report_type = Column(String(100), nullable=False)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    disclosure_date = Column(Date, nullable=False, index=True)
    meta_data = Column(JSON, nullable=True)  # metadata -> meta_data로 변경

    def __repr__(self):
        return f"<DartReport(corp_name='{self.corp_name}', title='{self.title}')>" 
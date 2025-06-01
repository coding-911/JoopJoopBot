import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor, Json

from joopjoop.rag import RAGPipeline
from joopjoop.dart.utils import parse_date

logger = logging.getLogger(__name__)

class DartCollector:
    """DART 문서 수집기"""
    
    def __init__(
        self,
        db_connection,
        rag_pipeline: Optional[RAGPipeline] = None,
        vector_store_enabled: bool = True
    ):
        self.db_conn = db_connection
        self.rag_pipeline = rag_pipeline
        self.vector_store_enabled = vector_store_enabled

    def process_document(self, document: Dict[str, Any]) -> bool:
        """
        DART 문서를 처리하고 저장
        
        Args:
            document: DART API로부터 받은 문서 데이터
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 날짜 처리 - datetime 객체로 파싱
            disclosure_date = parse_date(document['disclosure_date'])
            
            # 1. PostgreSQL에 원문 저장
            with self.db_conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO dart_reports (
                            corp_code, corp_name, receipt_no, report_type,
                            title, content, disclosure_date, meta_data
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        document['corp_code'],
                        document['corp_name'],
                        document['receipt_no'],
                        document['report_type'],
                        document['title'],
                        document['content'],
                        disclosure_date.strftime("%Y-%m-%d"),  # DB 저장 시 포맷팅
                        Json({
                            'dcm_no': document.get('dcm_no'),
                            'url': document.get('url'),
                            'file_name': document.get('file_name'),
                            'page_count': document.get('page_count')
                        })
                    ))
                    self.db_conn.commit()
                    logger.info(f"문서 저장 완료: {document['receipt_no']}")
                except psycopg2.errors.UniqueViolation:
                    self.db_conn.rollback()
                    logger.info(f"이미 존재하는 문서: {document['receipt_no']}")
                    return False

            # 2. 벡터 DB에 청크 저장 (옵션)
            if self.vector_store_enabled and self.rag_pipeline:
                meta_data = {
                    'corp_code': document['corp_code'],
                    'corp_name': document['corp_name'],
                    'receipt_no': document['receipt_no'],
                    'report_type': document['report_type'],
                    'title': document['title'],
                    'disclosure_date': disclosure_date.strftime("%Y-%m-%d")  # 메타데이터 저장 시 포맷팅
                }
                self.rag_pipeline.process_document(document)
                logger.info(f"벡터 저장소에 청크 저장 완료: {document['receipt_no']}")

            return True

        except Exception as e:
            logger.error(f"문서 처리 실패: {str(e)}")
            return False 
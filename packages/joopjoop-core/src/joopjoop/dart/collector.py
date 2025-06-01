import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor, Json

from joopjoop.rag import RAGPipeline

logger = logging.getLogger(__name__)

class DartCollector:
    def __init__(
        self,
        db_config: Dict[str, Any],
        rag_pipeline: Optional[RAGPipeline] = None,
        vector_store_enabled: bool = True
    ):
        self.db_config = db_config
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
            # 1. PostgreSQL에 원문 저장
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
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
                            datetime.strptime(document['disclosure_date'], '%Y-%m-%d').date(),
                            Json({
                                'dcm_no': document.get('dcm_no'),
                                'url': document.get('url'),
                                'file_name': document.get('file_name'),
                                'page_count': document.get('page_count')
                            })
                        ))
                        conn.commit()
                        logger.info(f"문서 저장 완료: {document['receipt_no']}")
                    except psycopg2.errors.UniqueViolation:
                        conn.rollback()
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
                    'disclosure_date': document['disclosure_date']
                }
                self.rag_pipeline.add_document(
                    document['content'],
                    meta_data=meta_data
                )
                logger.info(f"벡터 저장소에 청크 저장 완료: {document['receipt_no']}")

            return True

        except Exception as e:
            logger.error(f"문서 처리 실패: {str(e)}")
            return False 
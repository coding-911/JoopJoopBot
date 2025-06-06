import logging
import os
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class RAGPipeline:
    """RAG (Retrieval-Augmented Generation) 파이프라인"""
    
    def __init__(self, vector_store_path: Optional[str] = None):
        """
        RAG 파이프라인 초기화
        
        Args:
            vector_store_path: 벡터 DB 저장 경로. None인 경우 환경변수에서 가져옴
        """
        # 벡터 DB 경로 설정
        self.vector_store_path = vector_store_path or os.getenv("VECTOR_STORE_PATH")
        if not self.vector_store_path:
            raise ValueError(
                "벡터 DB 경로가 설정되지 않았습니다. "
                "vector_store_path 파라미터를 전달하거나 VECTOR_STORE_PATH 환경변수를 설정해주세요."
            )
        
        # 벡터 DB 디렉토리 생성
        Path(self.vector_store_path).mkdir(parents=True, exist_ok=True)
        
        # 임베딩 모델 초기화
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
        # FAISS 인덱스 초기화 (코사인 유사도 사용)
        self.embedding_size = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.embedding_size)  # 내적(코사인 유사도)
        
        # 청크 저장소
        self.chunks = []
        self.chunk_metadata = []
        
        # 인덱스 파일 경로
        self.index_path = Path(self.vector_store_path) / "index.faiss"
        self.chunks_path = Path(self.vector_store_path) / "chunks.npz"
        
        # 기존 인덱스가 있으면 로드
        self._load_index()
    
    def _load_index(self):
        """저장된 인덱스와 청크 로드"""
        try:
            if self.index_path.exists() and self.chunks_path.exists():
                # FAISS 인덱스 로드
                self.index = faiss.read_index(str(self.index_path))
                
                # 청크와 메타데이터 로드
                data = np.load(str(self.chunks_path), allow_pickle=True)
                self.chunks = data['chunks'].tolist()
                self.chunk_metadata = data['metadata'].tolist()
                
                logger.info(f"기존 인덱스 로드 완료: {len(self.chunks)}개 청크")
        except Exception as e:
            logger.warning(f"기존 인덱스 로드 실패, 새로운 인덱스 생성: {str(e)}")
            self.index = faiss.IndexFlatIP(self.embedding_size)
            self.chunks = []
            self.chunk_metadata = []
    
    def _save_index(self):
        """인덱스와 청크 저장"""
        try:
            # FAISS 인덱스 저장
            faiss.write_index(self.index, str(self.index_path))
            
            # 청크와 메타데이터 저장
            np.savez(
                str(self.chunks_path),
                chunks=np.array(self.chunks, dtype=object),
                metadata=np.array(self.chunk_metadata, dtype=object)
            )
            
            logger.info(f"인덱스 저장 완료: {len(self.chunks)}개 청크")
        except Exception as e:
            logger.error(f"인덱스 저장 실패: {str(e)}")

    def split_into_chunks(self, text: str, min_chunk_size: int = 100, max_chunk_size: int = 512) -> List[str]:
        """
        텍스트를 의미 있는 청크로 분할
        
        Args:
            text: 분할할 텍스트
            min_chunk_size: 최소 청크 크기
            max_chunk_size: 최대 청크 크기
            
        Returns:
            List[str]: 분할된 청크 목록
        """
        # 1. 문단 단위로 분할
        paragraphs = text.split('\n\n')
        
        # 2. 각 문단을 문장 단위로 분할하고 청크로 병합
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # 문장 단위로 분할 (마침표, 물음표, 느낌표 기준)
            sentences = re.split(r'[.!?]+', para)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # 문장이 너무 길면 적절한 크기로 분할
                if len(sentence) > max_chunk_size:
                    sub_chunks = [sentence[i:i + max_chunk_size] 
                                for i in range(0, len(sentence), max_chunk_size)]
                    for sub_chunk in sub_chunks:
                        if len(current_chunk) + len(sub_chunk) + 1 <= max_chunk_size:
                            current_chunk = (current_chunk + " " + sub_chunk).strip()
                        else:
                            if len(current_chunk) >= min_chunk_size:
                                chunks.append(current_chunk)
                            current_chunk = sub_chunk
                else:
                    if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                        current_chunk = (current_chunk + " " + sentence).strip()
                    else:
                        if len(current_chunk) >= min_chunk_size:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                        
        # 마지막 청크 추가
        if current_chunk and len(current_chunk) >= min_chunk_size:
            chunks.append(current_chunk)
            
        return chunks
        
    def process_document(self, document: Dict) -> None:
        """
        문서를 처리하여 청크로 분할하고 인덱싱
        
        Args:
            document: 공시 문서 (제목, 본문 등 포함)
        """
        if not document.get('content'):
            logger.warning("문서에 content가 없습니다.")
            return
            
        # 문서 메타데이터
        metadata = {
            'title': document.get('title', '제목 없음'),
            'corp_name': document.get('corp_name', '기업명 없음'),
            'receipt_no': document.get('receipt_no', ''),
            'dcm_no': document.get('dcm_no', ''),
            'disclosure_date': document.get('disclosure_date', '')
        }
        
        # 문서를 청크로 분할
        content = document['content']
        chunks = self.split_into_chunks(content)
        
        if not chunks:
            logger.warning("문서를 청크로 분할할 수 없습니다.")
            return
            
        # 청크 임베딩 및 인덱싱
        embeddings = self.model.encode(chunks, convert_to_tensor=False)  # numpy 배열로 변환
        
        # 임베딩 정규화 (코사인 유사도를 위해)
        faiss.normalize_L2(embeddings)
        
        # FAISS 인덱스에 추가
        self.index.add(embeddings)
        
        # 청크와 메타데이터 저장
        self.chunks.extend(chunks)
        self.chunk_metadata.extend([metadata] * len(chunks))
        
        # 인덱스 저장
        self._save_index()
        
        logger.debug(f"문서 처리 완료: {len(chunks)}개 청크 추가됨")
        
    def search_similar_chunks(self, query: str, k: int = 5) -> List[Dict]:
        """
        쿼리와 유사한 청크 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            
        Returns:
            List[Dict]: 검색 결과 목록. 각 결과는 청크 내용과 메타데이터 포함
        """
        if not self.chunks:
            raise ValueError("먼저 process_document()를 호출하여 문서를 추가해주세요.")
            
        # 쿼리 임베딩
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        
        # 임베딩 정규화
        faiss.normalize_L2(query_embedding)
        
        # 유사도 검색
        scores, indices = self.index.search(query_embedding, min(k, len(self.chunks)))
        
        # 결과 구성
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:  # FAISS가 결과를 찾지 못한 경우
                continue
            results.append({
                'content': self.chunks[idx],
                'metadata': self.chunk_metadata[idx],
                'score': float(score)
            })
            
        return results 
from typing import List, Optional
from langchain.schema import Document
from core.config import settings
from db.vector.chroma import ChromaClient

class RAGPipeline:
    def __init__(self, vector_store: ChromaClient):
        self.vector_store = vector_store
        self.llm_client = self._init_llm_client()

    def _init_llm_client(self):
        """
        Gemini API 클라이언트를 초기화합니다.
        """
        # TODO: Gemini API 클라이언트 구현
        pass

    async def process_question(
        self, 
        question: str, 
        chat_history: Optional[List[dict]] = None
    ) -> str:
        """
        사용자 질문을 처리하고 답변을 생성합니다.
        
        1. Vector DB에서 관련 문서 검색
        2. 컨텍스트 구성
        3. LLM으로 답변 생성
        """
        try:
            # 1. 관련 문서 검색
            relevant_docs = await self.vector_store.similarity_search(
                query=question,
                k=3  # 상위 3개 문서
            )
            
            # 2. 컨텍스트 구성
            context = self._prepare_context(relevant_docs)
            
            # 3. LLM 응답 생성
            response = await self.llm_client.generate_response(
                question=question,
                context=context,
                chat_history=chat_history
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"RAG 파이프라인 처리 중 오류 발생: {str(e)}")
    
    def _prepare_context(self, docs: List[Document]) -> str:
        """
        검색된 문서들을 컨텍스트로 구성합니다.
        """
        context_parts = []
        for doc in docs:
            context_parts.append(doc.page_content)
        
        return "\n\n".join(context_parts) 
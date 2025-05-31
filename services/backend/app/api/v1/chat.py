from fastapi import APIRouter, Depends, HTTPException
from typing import List

from schemas.chat import ChatRequest, ChatResponse
from services.chat.rag_pipeline import RAGPipeline
from dependencies.auth import get_current_user

router = APIRouter()

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    rag_pipeline: RAGPipeline = Depends()
):
    """
    금융 데이터 기반 질문에 대한 답변을 생성합니다.
    """
    try:
        response = await rag_pipeline.process_question(
            question=request.question,
            chat_history=request.chat_history
        )
        return ChatResponse(answer=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ChatResponse])
async def get_chat_history(
    current_user = Depends(get_current_user)
):
    """
    사용자의 채팅 히스토리를 조회합니다.
    """
    try:
        # TODO: 채팅 히스토리 조회 구현
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
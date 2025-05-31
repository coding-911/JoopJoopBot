from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import dart
from .core.config import settings


app = FastAPI(
    title="JoopJoopBot API",
    description="금융 데이터 기반 Q&A 및 리포트 생성 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(dart.router)

# API 라우터는 여기에 추가될 예정
# from .api.v1 import chat, report, financial
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(report.router, prefix="/api/v1/reports", tags=["reports"])
# app.include_router(financial.router, prefix="/api/v1/financial", tags=["financial"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=18000)

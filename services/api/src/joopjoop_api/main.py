from fastapi import FastAPI
from dotenv import load_dotenv
import os

from .routers import dart

# 환경변수 로드
load_dotenv()

app = FastAPI(
    title="JoopJoop API",
    description="주식 관련 공시 정보를 수집하고 분석하는 API",
    version="0.1.0"
)

# 라우터 등록
app.include_router(dart.router) 
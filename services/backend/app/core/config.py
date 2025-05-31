from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # 기본 설정
    PROJECT_NAME: str = "JoopJoopBot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str]
    
    # 데이터베이스 설정
    POSTGRES_USER: str = "joopjoop"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 15432
    POSTGRES_DB: str = "joopjoop"
    
    @property
    def DATABASE_URL(self) -> str:
        """데이터베이스 URL을 동적으로 생성"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Vector DB 설정
    VECTOR_DB_TYPE: str = "chroma"  # or "faiss"
    VECTOR_DB_PATH: str = "./vector_db"
    
    # DART API 설정
    DART_API_KEY: str
    
    # LLM 설정
    GEMINI_API_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
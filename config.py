"""
ZiTTA 설정 관리 모듈
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """애플리케이션 설정 클래스"""
    
    # Gemini API 설정
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-pro")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # 애플리케이션 설정
    APP_NAME = os.getenv("APP_NAME", "ZiTTA")
    APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
    
    # 데이터베이스 설정
    DB_PATH = os.path.join(os.path.dirname(__file__), "data", "zitta.db")
    
    @classmethod
    def validate(cls):
        """설정 유효성 검사"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return True


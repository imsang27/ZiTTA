"""
ZiTTA 설정 관리 모듈 (core 패키지 버전)
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트 디렉토리 (core/의 상위 디렉토리)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class Config:
    """애플리케이션 설정 클래스"""
    
    # LLM 설정
    USE_OFFLINE_MODE = os.getenv("USE_OFFLINE_MODE", "false").lower() == "true"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # 기본값은 README 가이드와 맞추어 gemini-2.5-flash 사용
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # 오프라인 모드 설정 (로컬 LLM 모델 경로 등)
    OFFLINE_MODEL_PATH = os.getenv("OFFLINE_MODEL_PATH", "")
    
    # 애플리케이션 설정
    APP_NAME = os.getenv("APP_NAME", "ZiTTA")
    APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
    
    # 데이터베이스 설정 (루트/data/zitta.db)
    DB_PATH = os.path.join(BASE_DIR, "data", "zitta.db")
    
    # 플러그인 설정 (루트/plugins)
    PLUGIN_DIR = os.path.join(BASE_DIR, "plugins")
    
    @classmethod
    def validate(cls):
        """설정 유효성 검사"""
        if not cls.USE_OFFLINE_MODE:
            if not cls.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        else:
            # 오프라인 모드에서는 API 키가 필요 없음
            if not cls.OFFLINE_MODEL_PATH:
                print("⚠️ 경고: 오프라인 모드가 활성화되었지만 OFFLINE_MODEL_PATH가 설정되지 않았습니다.")
                print("⚠️ 기본 규칙 기반 응답 시스템을 사용합니다.")
        return True



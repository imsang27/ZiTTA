"""
LLM API 클라이언트 모듈
Google Gemini API를 사용하여 자연어 명령을 처리합니다.
"""
import google.generativeai as genai
from config import Config

class LLMClient:
    """Google Gemini API 클라이언트"""
    
    def __init__(self):
        """LLM 클라이언트 초기화"""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.LLM_MODEL)
        self.temperature = Config.LLM_TEMPERATURE
        
        # 시스템 프롬프트
        self.system_prompt = """당신은 ZiTTA입니다. 사용자의 개인 AI 비서로서 똑똑하면서도 유머러스한 대화를 할 수 있습니다.
사용자의 명령을 이해하고 적절히 응답하세요. 할 일 관리, 메모, 파일 탐색 등의 작업을 도와줄 수 있습니다."""
        
        # Generation config 설정
        self.generation_config = genai.types.GenerationConfig(
            temperature=self.temperature
        )
        
        # 채팅 세션 초기화
        self.chat_session = None
    
    def chat(self, user_message: str, conversation_history: list = None) -> str:
        """
        사용자 메시지에 대한 응답 생성
        
        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 기록 (선택적)
            
        Returns:
            LLM 응답 문자열
        """
        try:
            # 채팅 세션이 없거나 대화 기록이 초기화된 경우 새 세션 시작
            if self.chat_session is None or not conversation_history:
                self.chat_session = self.model.start_chat(history=[])
                # 첫 메시지에 시스템 프롬프트 포함
                initial_prompt = f"{self.system_prompt}\n\n사용자: {user_message}"
                response = self.chat_session.send_message(initial_prompt)
                return response.text
            
            # 기존 대화 기록이 있는 경우, Gemini 형식으로 변환
            # conversation_history는 OpenAI 형식이므로 Gemini 형식으로 변환 필요
            # 하지만 Gemini는 자동으로 세션 히스토리를 관리하므로 단순히 메시지만 전송
            response = self.chat_session.send_message(user_message)
            return response.text
            
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"
    
    def process_command(self, command: str, context: dict = None) -> dict:
        """
        자연어 명령을 처리하고 적절한 작업을 수행
        
        Args:
            command: 사용자 명령
            context: 추가 컨텍스트 정보
            
        Returns:
            처리 결과 딕셔너리
        """
        # 간단한 명령 인식 (향후 확장 가능)
        command_lower = command.lower()
        
        # 할 일 관련 명령
        if any(keyword in command_lower for keyword in ["할 일", "todo", "해야", "해야 할"]):
            return {
                "type": "todo",
                "action": "create" if any(k in command_lower for k in ["추가", "만들", "생성"]) else "list",
                "command": command
            }
        
        # 일반 대화
        return {
            "type": "chat",
            "action": "respond",
            "command": command
        }


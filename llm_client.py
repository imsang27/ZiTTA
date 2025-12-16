"""
LLM API 클라이언트 모듈
Google Gemini API 또는 오프라인 모드를 사용하여 자연어 명령을 처리합니다.
"""
import google.generativeai as genai
from config import Config
import logging

# 로깅 설정 (디버깅용)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfflineLLM:
    """오프라인 모드 LLM (간단한 규칙 기반 응답)"""
    
    def __init__(self):
        """오프라인 LLM 초기화"""
        self.responses = {
            "인사": ["안녕하세요! 저는 ZiTTA입니다. 무엇을 도와드릴까요?", "반갑습니다! 오늘도 좋은 하루 되세요!"],
            "날씨": ["죄송하지만 오프라인 모드에서는 실시간 날씨 정보를 제공할 수 없습니다."],
            "시간": ["현재 시간을 확인하려면 시스템 시계를 확인해주세요."],
        }
    
    def generate_response(self, user_message: str) -> str:
        """간단한 규칙 기반 응답 생성"""
        message_lower = user_message.lower()
        
        # 키워드 기반 응답
        if any(word in message_lower for word in ["안녕", "하이", "헬로", "반가"]):
            import random
            return random.choice(self.responses["인사"])
        elif any(word in message_lower for word in ["날씨", "기온", "온도"]):
            return self.responses["날씨"][0]
        elif any(word in message_lower for word in ["시간", "몇 시"]):
            from datetime import datetime
            return f"현재 시간은 {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}입니다."
        else:
            return "오프라인 모드에서는 제한적인 응답만 가능합니다. 온라인 모드로 전환하시면 더 많은 기능을 사용하실 수 있습니다."

class LLMClient:
    """LLM 클라이언트 (온라인/오프라인 모드 지원)"""
    
    def __init__(self):
        """LLM 클라이언트 초기화"""
        self.use_offline = Config.USE_OFFLINE_MODE
        
        if self.use_offline:
            # 오프라인 모드
            self.offline_llm = OfflineLLM()
            self.model = None
            self.chat_session = None
            print("오프라인 모드로 실행 중입니다.")
        else:
            # 온라인 모드 (Gemini API)
            if not Config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
            
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            # 모델 초기화 시도
            try:
                # Generation config를 모델 초기화 시 설정
                self.generation_config = genai.types.GenerationConfig(
                    temperature=Config.LLM_TEMPERATURE
                )
                self.model = genai.GenerativeModel(
                    Config.LLM_MODEL,
                    generation_config=self.generation_config
                )
            except Exception as e:
                # 사용 가능한 모델 목록 가져오기
                available_models = self._get_available_models()
                error_msg = f"모델 '{Config.LLM_MODEL}'을 찾을 수 없습니다.\n\n"
                error_msg += f"오류: {str(e)}\n\n"
                if available_models:
                    error_msg += "사용 가능한 모델 목록:\n"
                    for model in available_models:
                        error_msg += f"  - {model}\n"
                else:
                    error_msg += "사용 가능한 모델을 가져올 수 없습니다. API 키를 확인하세요."
                raise ValueError(error_msg)
            
            self.temperature = Config.LLM_TEMPERATURE
            self.offline_llm = None
            
            # 채팅 세션 초기화
            self.chat_session = None
        
        # 시스템 프롬프트
        self.system_prompt = """당신은 ZiTTA입니다. 사용자의 개인 AI 비서로서 똑똑하면서도 유머러스한 대화를 할 수 있습니다.
사용자의 명령을 이해하고 적절히 응답하세요. 할 일 관리, 메모, 파일 탐색 등의 작업을 도와줄 수 있습니다."""
    
    def _get_available_models(self) -> list:
        """
        사용 가능한 Gemini 모델 목록 가져오기
        
        Returns:
            사용 가능한 모델 이름 리스트
        """
        try:
            models = genai.list_models()
            available_models = []
            for model in models:
                # GENERATE_CONTENT를 지원하는 모델만 필터링
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name.replace('models/', ''))
            return available_models
        except Exception as e:
            print(f"모델 목록을 가져오는 중 오류 발생: {e}")
            return []
    
    def chat(self, user_message: str, conversation_history: list = None) -> str:
        """
        사용자 메시지에 대한 응답 생성
        
        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 기록 (선택적)
            
        Returns:
            LLM 응답 문자열
        """
        if self.use_offline:
            # 오프라인 모드
            return self.offline_llm.generate_response(user_message)
        
        # 온라인 모드 (Gemini API)
        try:
            # 채팅 세션이 없거나 대화 기록이 초기화된 경우 새 세션 시작
            if self.chat_session is None or not conversation_history:
                self.chat_session = self.model.start_chat(history=[])
                # 첫 메시지에 시스템 프롬프트 포함
                initial_prompt = f"{self.system_prompt}\n\n사용자: {user_message}"
                # generation_config는 모델 초기화 시 설정되므로 별도로 전달하지 않음
                response = self.chat_session.send_message(initial_prompt)
            else:
                # 기존 대화 기록이 있는 경우, Gemini 형식으로 변환
                # conversation_history는 OpenAI 형식이므로 Gemini 형식으로 변환 필요
                # 하지만 Gemini는 자동으로 세션 히스토리를 관리하므로 단순히 메시지만 전송
                response = self.chat_session.send_message(user_message)
            
            # 응답 처리 - Gemini API는 response.text로 직접 접근 가능
            if response is None:
                logger.error("API 응답이 None입니다")
                return "응답을 받을 수 없습니다. 다시 시도해주세요."
            
            # response.text 속성으로 직접 접근 시도 (가장 일반적인 방법)
            try:
                if hasattr(response, 'text'):
                    response_text = response.text
                    logger.info(f"response.text로 응답 받음: 길이={len(response_text) if response_text else 0}")
                    if response_text and response_text.strip():
                        return response_text.strip()
                    else:
                        logger.warning("response.text가 비어있습니다")
            except Exception as text_error:
                logger.warning(f"response.text 접근 실패: {text_error}")
                # text 속성 접근 실패 시 다른 방법 시도
                pass
            
            # response.text가 없는 경우 대체 방법 시도
            # candidates를 통해 접근
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content'):
                            content = candidate.content
                            if hasattr(content, 'parts') and content.parts:
                                text_parts = []
                                for part in content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        text_parts.append(part.text)
                                if text_parts:
                                    return ''.join(text_parts).strip()
            except Exception as candidate_error:
                pass
            
            # 모든 방법 실패 시 - 실제 응답 객체 정보를 포함한 디버깅 메시지
            response_info = f"응답 타입: {type(response).__name__}"
            if hasattr(response, '__dict__'):
                response_info += f", 속성: {list(response.__dict__.keys())}"
            elif hasattr(response, '__class__'):
                response_info += f", 메서드: {[m for m in dir(response) if not m.startswith('_')][:10]}"
            
            return f"응답을 처리할 수 없습니다. {response_info}"
            
        except Exception as e:
            error_str = str(e)
            error_type = type(e).__name__
            logger.error(f"API 호출 중 오류 발생: {error_type} - {error_str}")
            
            # 할당량 초과 오류인지 확인
            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                error_msg = self._format_quota_error_message(error_str)
                return error_msg
            # 모델을 찾을 수 없는 오류인지 확인
            elif "not found" in error_str.lower() or "404" in error_str or "not supported" in error_str.lower():
                available_models = self._get_available_models()
                error_msg = self._format_model_error_message(error_str, available_models)
                return error_msg
            else:
                # 기타 오류 - 간단한 메시지만 반환
                return f"오류가 발생했습니다 ({error_type}): {error_str}"
    
    def _format_model_error_message(self, error_str: str, available_models: list) -> str:
        """
        모델 오류 메시지를 가독성 좋게 포맷팅
        
        Args:
            error_str: 오류 메시지
            available_models: 사용 가능한 모델 목록
            
        Returns:
            포맷팅된 오류 메시지
        """
        # 추천 모델 (안정적이고 일반적으로 사용되는 모델)
        # 가이드는 주로 gemini-2.5-flash / gemini-2.5-flash-lite 사용을 권장
        recommended_models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
            "gemini-flash-latest",
            "gemini-pro-latest",
        ]
        
        # 모델 그룹화
        recommended = []
        gemini_models = []
        gemma_models = []
        preview_models = []
        other_models = []
        
        for model in available_models:
            if model in recommended_models:
                recommended.append(model)
            elif model.startswith("gemini-"):
                if "preview" in model.lower() or "exp" in model.lower():
                    preview_models.append(model)
                else:
                    gemini_models.append(model)
            elif model.startswith("gemma-"):
                gemma_models.append(model)
            else:
                other_models.append(model)
        
        # 간단한 HTML 형식으로 포맷팅 (기본 태그만 사용)
        error_msg = f"""<b>❌ 모델 오류</b><br>
<pre style="color: #666; font-size: 0.9em; white-space: pre-wrap;">{error_str}</pre>
<br>
<b>📋 사용 가능한 모델 목록</b><br><br>"""
        
        # 추천 모델 섹션
        if recommended:
            error_msg += f"""<b>⭐ 추천 모델 (안정적)</b><br>"""
            for model in sorted(recommended):
                error_msg += f"""&nbsp;&nbsp;&nbsp;&nbsp;• {model}<br>"""
            error_msg += "<br>"
        
        # Gemini 일반 모델
        if gemini_models:
            error_msg += f"""<b>🤖 Gemini 모델</b><br>"""
            for model in sorted(gemini_models):
                error_msg += f"""&nbsp;&nbsp;&nbsp;&nbsp;• {model}<br>"""
            error_msg += "<br>"
        
        # Gemma 모델
        if gemma_models:
            error_msg += f"""<b>💎 Gemma 모델</b><br>"""
            for model in sorted(gemma_models):
                error_msg += f"""&nbsp;&nbsp;&nbsp;&nbsp;• {model}<br>"""
            error_msg += "<br>"
        
        # Preview/Experimental 모델
        if preview_models:
            error_msg += f"""<b>🔬 Preview/Experimental 모델</b><br>"""
            for model in sorted(preview_models):
                error_msg += f"""&nbsp;&nbsp;&nbsp;&nbsp;• {model}<br>"""
            error_msg += "<br>"
        
        # 기타 모델
        if other_models:
            error_msg += f"""<b>📦 기타 모델</b><br>"""
            for model in sorted(other_models):
                error_msg += f"""&nbsp;&nbsp;&nbsp;&nbsp;• {model}<br>"""
            error_msg += "<br>"
        
        error_msg += f"""<br>
<b>💡 해결 방법</b><br>
&nbsp;&nbsp;&nbsp;&nbsp;1. .env 파일을 열어주세요<br>
&nbsp;&nbsp;&nbsp;&nbsp;2. LLM_MODEL 값을 위 목록 중 하나로 변경하세요<br>
&nbsp;&nbsp;&nbsp;&nbsp;3. 추천: <code>gemini-2.5-flash</code> 또는 <code>gemini-2.5-flash-lite</code><br>
&nbsp;&nbsp;&nbsp;&nbsp;4. 현재 설정: <b>{Config.LLM_MODEL}</b>"""
        
        if not available_models:
            error_msg = f"""<b>❌ 모델 오류</b><br>
<pre style="color: #666; white-space: pre-wrap;">{error_str}</pre>
<br>
<b>⚠️ 사용 가능한 모델을 가져올 수 없습니다.</b><br>
API 키를 확인하세요."""
        
        return error_msg
    
    def _format_quota_error_message(self, error_str: str) -> str:
        """
        할당량 초과 오류 메시지를 가독성 좋게 포맷팅
        
        Args:
            error_str: 오류 메시지
            
        Returns:
            포맷팅된 오류 메시지
        """
        import re
        
        # 재시도 시간 추출
        retry_match = re.search(r'Please retry in ([\d.]+)s', error_str)
        retry_time = retry_match.group(1) if retry_match else None
        
        # 모델 이름 추출
        model_match = re.search(r'model: ([a-z0-9-]+)', error_str)
        model_name = model_match.group(1) if model_match else Config.LLM_MODEL
        
        error_msg = f"""<b>⚠️ API 할당량 초과</b><br><br>
<b>문제:</b> Gemini API의 무료 티어 할당량을 초과했습니다.<br><br>
<b>현재 모델:</b> {model_name}<br>"""
        
        if retry_time:
            minutes = int(float(retry_time) // 60)
            seconds = int(float(retry_time) % 60)
            if minutes > 0:
                retry_text = f"{minutes}분 {seconds}초"
            else:
                retry_text = f"{seconds}초"
            error_msg += f"""<b>재시도 가능 시간:</b> 약 {retry_text} 후<br><br>"""
        
        error_msg += f"""<b>💡 해결 방법:</b><br>
&nbsp;&nbsp;&nbsp;&nbsp;1. <b>잠시 기다리기:</b> 할당량이 리셋될 때까지 기다리세요 (보통 1분 또는 1일 단위)<br>
&nbsp;&nbsp;&nbsp;&nbsp;2. <b>다른 모델 사용:</b> 할당량이 더 많은 모델로 변경하세요<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;추천: <code>gemini-2.5-flash</code> 또는 <code>gemini-2.5-flash-lite</code><br>
&nbsp;&nbsp;&nbsp;&nbsp;3. <b>유료 플랜으로 업그레이드:</b> 더 높은 할당량을 사용하려면 Google AI Studio에서 플랜을 업그레이드하세요<br><br>
<b>📚 자세한 정보:</b><br>
&nbsp;&nbsp;&nbsp;&nbsp;• 할당량 정보: <a href="https://ai.google.dev/gemini-api/docs/rate-limits">https://ai.google.dev/gemini-api/docs/rate-limits</a><br>
&nbsp;&nbsp;&nbsp;&nbsp;• 사용량 확인: <a href="https://ai.dev/usage?tab=rate-limit">https://ai.dev/usage?tab=rate-limit</a>"""
        
        return error_msg
    
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
        
        # 메모 관련 명령
        if any(keyword in command_lower for keyword in ["메모", "memo", "노트", "note"]):
            return {
                "type": "memo",
                "action": "create" if any(k in command_lower for k in ["추가", "만들", "생성", "작성"]) else "list",
                "command": command
            }
        
        # 파일 관련 명령
        if any(keyword in command_lower for keyword in ["파일", "file", "폴더", "folder", "디렉토리"]):
            return {
                "type": "file",
                "action": "list",
                "command": command
            }
        
        # 일반 대화
        return {
            "type": "chat",
            "action": "respond",
            "command": command
        }


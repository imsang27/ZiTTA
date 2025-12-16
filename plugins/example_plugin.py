"""
ZiTTA 플러그인 예제
플러그인 개발 가이드 및 예제 코드

사용 방법:
1. 이 파일을 plugins/ 디렉토리에 복사
2. PluginBase를 상속하여 플러그인 클래스 생성
3. handle_command 메서드를 구현하여 명령 처리
4. 애플리케이션 재시작 시 자동으로 로드됨
"""
import sys
import os

# 상위 디렉토리에서 plugin_manager import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugin_manager import PluginBase

class ExamplePlugin(PluginBase):
    """예제 플러그인"""
    
    def __init__(self):
        super().__init__("ExamplePlugin", "1.0.0")
    
    def on_load(self):
        """플러그인 로드 시 호출"""
        print(f"플러그인 '{self.name}' v{self.version} 로드됨")
    
    def on_unload(self):
        """플러그인 언로드 시 호출"""
        print(f"플러그인 '{self.name}' 언로드됨")
    
    def handle_command(self, command: str, context: dict = None) -> dict:
        """
        명령 처리
        
        Args:
            command: 사용자 명령
            context: 컨텍스트 정보
            
        Returns:
            처리 결과 또는 None (처리하지 않음)
        """
        command_lower = command.lower()
        
        # "안녕" 명령 처리 예제
        if "안녕" in command_lower or "hello" in command_lower:
            return {
                "type": "plugin_response",
                "plugin": self.name,
                "response": "안녕하세요! 예제 플러그인입니다."
            }
        
        # 처리하지 않으면 None 반환
        return None
    
    def get_commands(self) -> list:
        """지원하는 명령 목록"""
        return ["안녕", "hello"]


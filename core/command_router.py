"""
명령 라우팅 모듈
사용자 메시지를 분석하여 적절한 명령 타입과 액션을 결정합니다.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .types import Intent

class CommandRouter:
    """명령 라우터"""
    
    def __init__(self):
        """설정 파일에서 키워드 규칙을 로드"""
        config_path = Path(__file__).parent / "command_keywords.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # todo 키워드
        self.todo_keywords = config["todo"]["keywords"]
        self.todo_list_keywords = config["todo"]["list_keywords"]
        self.todo_create_words = config["todo"]["create_words"]
        
        # memo 키워드
        self.memo_keywords = config["memo"]["keywords"]
        self.memo_list_keywords = config["memo"]["list_keywords"]
        self.memo_create_words = config["memo"]["create_words"]
        
        # file 키워드
        self.file_keywords = config["file"]["keywords"]
        self.file_dir_keywords = config["file"]["dir_keywords"]
        self.file_file_keywords = config["file"]["file_keywords"]
    
    def route(self, message: str) -> Intent:
        """
        사용자 메시지를 분석하여 명령 타입과 액션을 반환
        
        Args:
            message: 사용자 메시지
            
        Returns:
            Intent 객체
        """
        message_lower = message.lower().strip()
        
        # 할 일 관련 명령
        if any(keyword in message_lower for keyword in self.todo_list_keywords):
            return Intent(type="todo", action="list", source="router")
        elif any(keyword in message_lower for keyword in self.todo_keywords):
            # action 판정: "추가/등록" 같은 동사는 action 판정에만 사용
            if any(word in message_lower for word in self.todo_create_words):
                return Intent(type="todo", action="create", source="router")
            # 단순히 "할 일"만 언급한 경우도 생성으로 간주
            return Intent(type="todo", action="create", source="router")
        
        # 메모 관련 명령
        if any(keyword in message_lower for keyword in self.memo_list_keywords):
            return Intent(type="memo", action="list", source="router")
        elif any(keyword in message_lower for keyword in self.memo_keywords):
            # action 판정: "추가/등록" 같은 동사는 action 판정에만 사용
            if any(word in message_lower for word in self.memo_create_words):
                return Intent(type="memo", action="create", source="router")
            return Intent(type="memo", action="create", source="router")
        
        # 파일 관련 명령 (범용 단어 "목록/리스트/보기" 제거)
        if any(keyword in message_lower for keyword in self.file_keywords):
            # 필터 판정: "폴더/디렉토리/directory" 포함 시 디렉토리만
            if any(keyword in message_lower for keyword in self.file_dir_keywords):
                return Intent(type="file", action="list", payload={"filter": "dir"}, source="router")
            # "파일/file"만 명시된 경우 파일만 (선택적, 기본은 all)
            elif any(keyword in message_lower for keyword in self.file_file_keywords):
                return Intent(type="file", action="list", payload={"filter": "all"}, source="router")
            # 기본값: 모두 표시
            return Intent(type="file", action="list", payload={"filter": "all"}, source="router")
        
        # 일반 대화
        return Intent(type="chat", action=None, source="router")

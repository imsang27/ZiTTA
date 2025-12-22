"""
명령 라우팅 모듈
사용자 메시지를 분석하여 적절한 명령 타입과 액션을 결정합니다.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class CommandResult:
    """명령 라우팅 결과"""
    type: str  # "todo", "memo", "file", "chat"
    action: Optional[str] = None  # "create", "list" 등
    payload: Optional[Dict[str, Any]] = None  # 추가 데이터 (선택적)

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
    
    def route(self, message: str) -> CommandResult:
        """
        사용자 메시지를 분석하여 명령 타입과 액션을 반환
        
        Args:
            message: 사용자 메시지
            
        Returns:
            CommandResult 객체
        """
        message_lower = message.lower().strip()
        
        # 할 일 관련 명령
        if any(keyword in message_lower for keyword in self.todo_list_keywords):
            return CommandResult(type="todo", action="list")
        elif any(keyword in message_lower for keyword in self.todo_keywords):
            # action 판정: "추가/등록" 같은 동사는 action 판정에만 사용
            if any(word in message_lower for word in self.todo_create_words):
                return CommandResult(type="todo", action="create")
            # 단순히 "할 일"만 언급한 경우도 생성으로 간주
            return CommandResult(type="todo", action="create")
        
        # 메모 관련 명령
        if any(keyword in message_lower for keyword in self.memo_list_keywords):
            return CommandResult(type="memo", action="list")
        elif any(keyword in message_lower for keyword in self.memo_keywords):
            # action 판정: "추가/등록" 같은 동사는 action 판정에만 사용
            if any(word in message_lower for word in self.memo_create_words):
                return CommandResult(type="memo", action="create")
            return CommandResult(type="memo", action="create")
        
        # 파일 관련 명령 (범용 단어 "목록/리스트/보기" 제거)
        if any(keyword in message_lower for keyword in self.file_keywords):
            return CommandResult(type="file", action="list")
        
        # 일반 대화
        return CommandResult(type="chat", action=None)

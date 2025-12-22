"""
명령 라우팅 모듈
사용자 메시지를 분석하여 적절한 명령 타입과 액션을 결정합니다.
"""
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class CommandResult:
    """명령 라우팅 결과"""
    type: str  # "todo", "memo", "file", "chat"
    action: Optional[str] = None  # "create", "list" 등
    payload: Optional[Any] = None  # 추가 데이터 (선택적)


class CommandRouter:
    """명령 라우터"""
    
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
        todo_keywords = ["할 일", "할일", "todo", "해야 할", "해야할", "해야"]
        todo_list_keywords = ["할 일 목록", "할일 목록", "할 일 리스트", "할일 리스트", "할 일 보기", "할일 보기"]
        
        if any(keyword in message_lower for keyword in todo_list_keywords):
            return CommandResult(type="todo", action="list")
        elif any(keyword in message_lower for keyword in todo_keywords):
            # action 판정: "추가/등록" 같은 동사는 action 판정에만 사용
            if any(word in message_lower for word in ["추가", "등록", "만들", "생성", "create", "add"]):
                return CommandResult(type="todo", action="create")
            # 단순히 "할 일"만 언급한 경우도 생성으로 간주
            return CommandResult(type="todo", action="create")
        
        # 메모 관련 명령
        memo_keywords = ["메모", "memo", "기억", "저장"]
        memo_list_keywords = ["메모 목록", "메모 리스트", "메모 보기", "메모 검색"]
        
        if any(keyword in message_lower for keyword in memo_list_keywords):
            return CommandResult(type="memo", action="list")
        elif any(keyword in message_lower for keyword in memo_keywords):
            # action 판정: "추가/등록" 같은 동사는 action 판정에만 사용
            if any(word in message_lower for word in ["추가", "등록", "만들", "생성", "create", "add"]):
                return CommandResult(type="memo", action="create")
            return CommandResult(type="memo", action="create")
        
        # 파일 관련 명령 (범용 단어 "목록/리스트/보기" 제거)
        file_keywords = ["파일", "file", "폴더", "디렉토리", "directory"]
        
        if any(keyword in message_lower for keyword in file_keywords):
            return CommandResult(type="file", action="list")
        
        # 일반 대화
        return CommandResult(type="chat", action=None)


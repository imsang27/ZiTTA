"""
ZiTTAEngine 단위 테스트

테스트 실행 방법:
    pytest -q

또는 상세 출력:
    pytest -v

Windows에서도 동작합니다.
"""

import pytest
from typing import Optional, List, Dict, Any
from core.engine import ZiTTAEngine
from core.types import Intent

# ============================================================================
# Fake 구현체들
# ============================================================================

class FakePluginManager:
    """Fake 플러그인 관리자"""
    
    def __init__(self, return_intent: Optional[Intent] = None):
        """
        Args:
            return_intent: handle_command 호출 시 반환할 Intent (None이면 처리하지 않음)
        """
        self.return_intent = return_intent
        self.last_message = None
    
    def handle_command(self, message: str) -> Optional[Intent]:
        """명령 처리 (테스트용)"""
        self.last_message = message
        return self.return_intent


class FakeCommandRouter:
    """Fake 명령 라우터"""
    
    def __init__(self, return_intent: Intent):
        """
        Args:
            return_intent: route 호출 시 반환할 Intent
        """
        self.return_intent = return_intent
        self.last_message = None
    
    def route(self, message: str) -> Intent:
        """명령 라우팅 (테스트용)"""
        self.last_message = message
        return self.return_intent


class FakeTodoManager:
    """Fake 할 일 관리자"""
    
    def __init__(self):
        self.todos = []
    
    def add_todo(self, title: str):
        """할 일 추가 (테스트용)"""
        self.todos.append({"title": title, "completed": False})
    
    def get_todos(self, completed: bool = False) -> List[Dict]:
        """할 일 목록 조회 (테스트용)"""
        if completed:
            return [todo for todo in self.todos if todo["completed"]]
        else:
            return [todo for todo in self.todos if not todo["completed"]]


class FakeMemoManager:
    """Fake 메모 관리자"""
    
    def __init__(self):
        self.memos = []
    
    def add_memo(self, title: str):
        """메모 추가 (테스트용)"""
        self.memos.append({"title": title})
    
    def get_memos(self) -> List[Dict]:
        """메모 목록 조회 (테스트용)"""
        return self.memos


class FakeFileExplorer:
    """Fake 파일 탐색기"""
    
    def __init__(self, return_items: List[Dict]):
        """
        Args:
            return_items: list_directory 호출 시 반환할 항목 리스트
                          각 항목은 {"name": str, "is_directory": bool} 형태
        """
        self.return_items = return_items
        self.last_path = None
    
    def list_directory(self, path: str = None) -> List[Dict]:
        """디렉토리 목록 조회 (테스트용)"""
        self.last_path = path
        return self.return_items


# ============================================================================
# 테스트 케이스들
# ============================================================================

def test_plugin_priority():
    """
    (1) plugin 우선순위 테스트
    plugin_manager가 Intent(type="plugin", payload={"plugin":"X","response":"R"}) 반환하면
    engine.handle() 결과가 type="plugin", needs_llm=False, response="R", plugin_name="X" 여야 함.
    """
    # 준비
    plugin_intent = Intent(
        type="plugin",
        payload={"plugin": "TestPlugin", "response": "플러그인 응답입니다"}
    )
    fake_plugin_manager = FakePluginManager(return_intent=plugin_intent)
    fake_router = FakeCommandRouter(return_intent=Intent(type="chat"))
    fake_todo = FakeTodoManager()
    fake_memo = FakeMemoManager()
    fake_file = FakeFileExplorer(return_items=[])
    
    engine = ZiTTAEngine(
        command_router=fake_router,
        plugin_manager=fake_plugin_manager,
        todo_manager=fake_todo,
        memo_manager=fake_memo,
        file_explorer=fake_file,
        llm_client=None
    )
    
    # 실행
    result = engine.handle("테스트 메시지")
    
    # 검증
    assert result["type"] == "plugin"
    assert result["needs_llm"] is False
    assert result["response"] == "플러그인 응답입니다"
    assert result["plugin_name"] == "TestPlugin"
    assert result["llm_prompt"] is None


def test_chat_fallback():
    """
    (2) chat fallback 테스트
    router가 Intent(type="chat") 반환하면
    engine.handle() 결과 needs_llm=True, llm_prompt가 원문 message 여야 함.
    """
    # 준비
    fake_plugin_manager = FakePluginManager(return_intent=None)  # 플러그인 처리 안 함
    fake_router = FakeCommandRouter(return_intent=Intent(type="chat"))
    fake_todo = FakeTodoManager()
    fake_memo = FakeMemoManager()
    fake_file = FakeFileExplorer(return_items=[])
    
    engine = ZiTTAEngine(
        command_router=fake_router,
        plugin_manager=fake_plugin_manager,
        todo_manager=fake_todo,
        memo_manager=fake_memo,
        file_explorer=fake_file,
        llm_client=None
    )
    
    # 실행
    test_message = "안녕하세요, 오늘 날씨가 어때요?"
    result = engine.handle(test_message)
    
    # 검증
    assert result["type"] == "chat"
    assert result["needs_llm"] is True
    assert result["llm_prompt"] == test_message
    assert result["response"] is None


def test_todo_create():
    """
    (3) todo create 테스트
    router가 Intent(type="todo", action="create") 반환하면
    engine.handle() 결과 type="todo", needs_llm=True, llm_prompt에 "할 일 제목" 추출 프롬프트가 포함되어야 함.
    """
    # 준비
    fake_plugin_manager = FakePluginManager(return_intent=None)
    fake_router = FakeCommandRouter(return_intent=Intent(type="todo", action="create"))
    fake_todo = FakeTodoManager()
    fake_memo = FakeMemoManager()
    fake_file = FakeFileExplorer(return_items=[])
    
    engine = ZiTTAEngine(
        command_router=fake_router,
        plugin_manager=fake_plugin_manager,
        todo_manager=fake_todo,
        memo_manager=fake_memo,
        file_explorer=fake_file,
        llm_client=None
    )
    
    # 실행
    test_message = "프로젝트 문서 작성하기"
    result = engine.handle(test_message)
    
    # 검증
    assert result["type"] == "todo"
    assert result["action"] == "create"
    assert result["needs_llm"] is True
    assert "할 일 제목" in result["llm_prompt"]
    assert test_message in result["llm_prompt"]
    assert result["response"] is None


def test_memo_create():
    """
    (4) memo create 테스트
    router가 Intent(type="memo", action="create") 반환하면
    engine.handle() 결과 type="memo", needs_llm=True, llm_prompt에 "메모 제목" 추출 프롬프트가 포함되어야 함.
    """
    # 준비
    fake_plugin_manager = FakePluginManager(return_intent=None)
    fake_router = FakeCommandRouter(return_intent=Intent(type="memo", action="create"))
    fake_todo = FakeTodoManager()
    fake_memo = FakeMemoManager()
    fake_file = FakeFileExplorer(return_items=[])
    
    engine = ZiTTAEngine(
        command_router=fake_router,
        plugin_manager=fake_plugin_manager,
        todo_manager=fake_todo,
        memo_manager=fake_memo,
        file_explorer=fake_file,
        llm_client=None
    )
    
    # 실행
    test_message = "회의록 작성하기"
    result = engine.handle(test_message)
    
    # 검증
    assert result["type"] == "memo"
    assert result["action"] == "create"
    assert result["needs_llm"] is True
    assert "메모 제목" in result["llm_prompt"]
    assert test_message in result["llm_prompt"]
    assert result["response"] is None


def test_file_list_all():
    """
    (5) file list all 테스트
    router가 Intent(type="file", action="list", payload={"filter":"all"}) 반환하고
    file_explorer.list_directory가 dir/file 혼합을 반환하면, engine.handle() 결과 payload/filter가 유지되어야 함
    (표시는 GUI에서 하므로 engine은 최소한 filter payload를 dict에 포함시키는지 확인).
    """
    # 준비
    fake_plugin_manager = FakePluginManager(return_intent=None)
    fake_router = FakeCommandRouter(
        return_intent=Intent(type="file", action="list", payload={"filter": "all"})
    )
    fake_todo = FakeTodoManager()
    fake_memo = FakeMemoManager()
    # dir/file 혼합 반환
    fake_file = FakeFileExplorer(return_items=[
        {"name": "folder1", "is_directory": True},
        {"name": "file1.txt", "is_directory": False},
        {"name": "folder2", "is_directory": True},
        {"name": "file2.py", "is_directory": False}
    ])
    
    engine = ZiTTAEngine(
        command_router=fake_router,
        plugin_manager=fake_plugin_manager,
        todo_manager=fake_todo,
        memo_manager=fake_memo,
        file_explorer=fake_file,
        llm_client=None
    )
    
    # 실행
    result = engine.handle("파일 목록 보기", current_directory=".")
    
    # 검증
    assert result["type"] == "file"
    assert result["action"] == "list"
    assert result["needs_llm"] is False
    assert "payload" in result
    assert result["payload"]["filter"] == "all"
    assert "response" in result  # response 키는 반드시 존재
    assert result["response"] is None or isinstance(result["response"], str)  # None 또는 str 허용


def test_file_list_dir():
    """
    (6) file list dir 테스트
    router가 Intent(type="file", action="list", payload={"filter":"dir"}) 반환하면
    engine.handle() 결과 payload.filter가 "dir"로 유지되어야 함.
    """
    # 준비
    fake_plugin_manager = FakePluginManager(return_intent=None)
    fake_router = FakeCommandRouter(
        return_intent=Intent(type="file", action="list", payload={"filter": "dir"})
    )
    fake_todo = FakeTodoManager()
    fake_memo = FakeMemoManager()
    fake_file = FakeFileExplorer(return_items=[
        {"name": "folder1", "is_directory": True},
        {"name": "file1.txt", "is_directory": False},
        {"name": "folder2", "is_directory": True}
    ])
    
    engine = ZiTTAEngine(
        command_router=fake_router,
        plugin_manager=fake_plugin_manager,
        todo_manager=fake_todo,
        memo_manager=fake_memo,
        file_explorer=fake_file,
        llm_client=None
    )
    
    # 실행
    result = engine.handle("폴더 목록 보기", current_directory=".")
    
    # 검증
    assert result["type"] == "file"
    assert result["action"] == "list"
    assert result["needs_llm"] is False
    assert "payload" in result
    assert result["payload"]["filter"] == "dir"
    assert "response" in result  # response 키는 반드시 존재
    assert result["response"] is None or isinstance(result["response"], str)  # None 또는 str 허용


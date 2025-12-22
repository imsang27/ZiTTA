"""
ZiTTA 엔진 모듈
메시지 처리 로직을 중앙화하여 core 라이브러리화를 위한 기반을 제공합니다.
"""
from typing import Dict, Optional, Any
from .command_router import CommandRouter
from .plugin_manager import PluginManager
from .todo_manager import TodoManager
from .memo_manager import MemoManager
from .file_explorer import FileExplorer
from .llm_client import LLMClient
from .types import Intent


class ZiTTAEngine:
    """ZiTTA 메시지 처리 엔진"""
    
    def __init__(
        self,
        command_router: Optional[CommandRouter] = None,
        plugin_manager: Optional[PluginManager] = None,
        todo_manager: Optional[TodoManager] = None,
        memo_manager: Optional[MemoManager] = None,
        file_explorer: Optional[FileExplorer] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        ZiTTA 엔진 초기화
        
        Args:
            command_router: 명령 라우터 (None이면 생성)
            plugin_manager: 플러그인 관리자 (None이면 생성)
            todo_manager: 할 일 관리자 (None이면 생성)
            memo_manager: 메모 관리자 (None이면 생성)
            file_explorer: 파일 탐색기 (None이면 생성)
            llm_client: LLM 클라이언트 (None이면 생성)
        """
        self.command_router = command_router or CommandRouter()
        self.plugin_manager = plugin_manager or PluginManager()
        if plugin_manager is None:
            self.plugin_manager.load_plugins()
        self.todo_manager = todo_manager or TodoManager()
        self.memo_manager = memo_manager or MemoManager()
        self.file_explorer = file_explorer or FileExplorer()
        self.llm_client = llm_client
    
    def handle(self, message: str, current_directory: str = None) -> Dict[str, Any]:
        """
        메시지 처리 (처리 우선순위: plugin -> router -> local -> llm)
        
        Args:
            message: 사용자 메시지
            current_directory: 현재 작업 디렉토리 (파일 명령 처리 시 필요)
            
        Returns:
            처리 결과 딕셔너리:
            {
                "type": "plugin" | "todo" | "memo" | "file" | "chat",
                "action": "create" | "list" | None,
                "response": str,  # 응답 텍스트
                "needs_llm": bool,  # LLM 처리가 필요한지 (todo/memo create 시)
                "llm_prompt": str,  # LLM에 전달할 프롬프트 (needs_llm=True일 때)
                "payload": dict,  # 추가 데이터 (file filter 등)
                "plugin_name": str,  # 플러그인 이름 (type="plugin"일 때)
            }
        """
        # 1. 플러그인 처리 먼저 시도
        plugin_intent = self.plugin_manager.handle_command(message)
        if plugin_intent:
            return self._intent_to_dict(plugin_intent, message)
        
        # 2. 명령 라우팅
        routed = self.command_router.route(message)
        
        # 3. 로컬 처리 (todo/memo/file)
        if routed.type == "todo":
            return self._handle_todo(routed, message)
        elif routed.type == "memo":
            return self._handle_memo(routed, message)
        elif routed.type == "file":
            return self._handle_file(routed, current_directory or ".")
        else:
            # 4. 일반 대화 (LLM fallback)
            return self._intent_to_dict(routed, message)
    
    def _intent_to_dict(self, intent: Intent, message: str) -> Dict[str, Any]:
        """
        Intent를 GUI에서 사용할 수 있는 dict 형태로 변환
        
        Args:
            intent: Intent 객체
            message: 원본 메시지 (LLM 프롬프트 생성 시 필요)
            
        Returns:
            GUI용 딕셔너리
        """
        result = {
            "type": intent.type,
            "action": intent.action,
            "payload": intent.payload,
            "plugin_name": None
        }
        
        # Intent 타입별 처리
        if intent.type == "plugin":
            # 플러그인 응답
            if intent.payload:
                result["response"] = intent.payload.get("response", "")
                result["plugin_name"] = intent.payload.get("plugin", "Unknown")
            result["needs_llm"] = False
            result["llm_prompt"] = None
        elif intent.type == "chat":
            # 일반 대화 (LLM 필요)
            result["response"] = None
            result["needs_llm"] = True
            result["llm_prompt"] = message
        else:
            # todo/memo/file는 각각의 _handle_* 메서드에서 처리
            # 여기서는 기본값만 설정
            result["response"] = None
            result["needs_llm"] = False
            result["llm_prompt"] = None
        
        return result
    
    def _handle_todo(self, routed: Intent, message: str) -> Dict[str, Any]:
        """할 일 관련 명령 처리"""
        if routed.action == "create":
            # LLM이 할 일을 추출하도록 요청
            todo_prompt = f"다음 명령에서 할 일 제목을 추출해주세요. 제목만 간단히 답변하세요: {message}"
            return {
                "type": "todo",
                "action": "create",
                "response": None,  # LLM 응답 후 처리
                "needs_llm": True,
                "llm_prompt": todo_prompt,
                "payload": None,
                "plugin_name": None
            }
        else:
            # 할 일 목록 조회
            todos = self.todo_manager.get_todos(completed=False)
            if todos:
                todo_list = "\n".join([f"- {todo['title']}" for todo in todos])
                response = f"현재 할 일 목록:\n{todo_list}"
            else:
                response = "할 일이 없습니다."
            
            return {
                "type": "todo",
                "action": "list",
                "response": response,
                "needs_llm": False,
                "llm_prompt": None,
                "payload": None,
                "plugin_name": None
            }
    
    def _handle_memo(self, routed: Intent, message: str) -> Dict[str, Any]:
        """메모 관련 명령 처리"""
        if routed.action == "create":
            # LLM이 메모 제목을 추출하도록 요청
            memo_prompt = f"다음 명령에서 메모 제목을 추출해주세요. 제목만 간단히 답변하세요: {message}"
            return {
                "type": "memo",
                "action": "create",
                "response": None,  # LLM 응답 후 처리
                "needs_llm": True,
                "llm_prompt": memo_prompt,
                "payload": None,
                "plugin_name": None
            }
        else:
            # 메모 목록 조회
            memos = self.memo_manager.get_memos()
            if memos:
                memo_list = "\n".join([f"- {memo['title']}" for memo in memos[:10]])
                response = f"현재 메모 목록 (최근 10개):\n{memo_list}"
            else:
                response = "메모가 없습니다."
            
            return {
                "type": "memo",
                "action": "list",
                "response": response,
                "needs_llm": False,
                "llm_prompt": None,
                "payload": None,
                "plugin_name": None
            }
    
    def _handle_file(self, routed: Intent, current_directory: str) -> Dict[str, Any]:
        """파일 관련 명령 처리"""
        items = self.file_explorer.list_directory(current_directory)
        if items:
            # payload의 filter에 따라 필터링
            filter_type = routed.payload.get("filter", "all") if routed.payload else "all"
            if filter_type == "dir":
                items = [item for item in items if item["is_directory"]]
            elif filter_type == "file":
                items = [item for item in items if not item["is_directory"]]
            # filter_type == "all"이거나 None이면 필터링 없음
            
            if items:
                file_list = "\n".join([f"- {'📁' if item['is_directory'] else '📄'} {item['name']}" for item in items[:20]])
                filter_text = "폴더만" if filter_type == "dir" else "파일만" if filter_type == "file" else "전체"
                response = f"현재 디렉토리 ({current_directory}) 내용 ({filter_text}):\n{file_list}"
            else:
                filter_text = "폴더" if filter_type == "dir" else "파일" if filter_type == "file" else "항목"
                response = f"{filter_text}이(가) 없습니다."
        else:
            response = "파일이 없습니다."
        
        return {
            "type": "file",
            "action": "list",
            "response": response,
            "needs_llm": False,
            "llm_prompt": None,
            "payload": {"filter": routed.payload.get("filter", "all") if routed.payload else "all"},
            "plugin_name": None
        }
    
    def process_llm_response(self, llm_response: str, result_type: str, action: str) -> Dict[str, Any]:
        """
        LLM 응답을 처리하여 실제 작업 수행 (todo/memo create 시)
        
        Args:
            llm_response: LLM 응답 텍스트
            result_type: 결과 타입 ("todo" 또는 "memo")
            action: 액션 ("create")
            
        Returns:
            처리 결과 딕셔너리
        """
        if result_type == "todo" and action == "create":
            todo_title = llm_response.strip()
            if todo_title:
                self.todo_manager.add_todo(todo_title)
                return {
                    "type": "todo",
                    "action": "create",
                    "response": f"할 일 '{todo_title}'을 추가했습니다.",
                    "needs_llm": False,
                    "llm_prompt": None,
                    "payload": None,
                    "plugin_name": None
                }
        elif result_type == "memo" and action == "create":
            memo_title = llm_response.strip()
            if memo_title:
                self.memo_manager.add_memo(memo_title)
                return {
                    "type": "memo",
                    "action": "create",
                    "response": f"메모 '{memo_title}'을 추가했습니다.",
                    "needs_llm": False,
                    "llm_prompt": None,
                    "payload": None,
                    "plugin_name": None
                }
        
        return {
            "type": result_type,
            "action": action,
            "response": llm_response,
            "needs_llm": False,
            "llm_prompt": None,
            "payload": None,
            "plugin_name": None
        }


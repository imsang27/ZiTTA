"""
ZiTTA 메인 GUI 창
PyQt6를 사용하여 구현된 메인 인터페이스
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QMessageBox, QTabWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import json

# 상위 디렉토리에서 모듈 import
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import LLMClient
from core.todo_manager import TodoManager
from core.memo_manager import MemoManager
from core.file_explorer import FileExplorer
from core.voice_handler import VoiceHandler
from core.plugin_manager import PluginManager
from core.command_router import CommandRouter

class LLMWorker(QThread):
    """LLM 응답을 비동기로 처리하는 워커 스레드"""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, llm_client, message, history):
        super().__init__()
        self.llm_client = llm_client
        self.message = message
        self.history = history
    
    def run(self):
        try:
            response = self.llm_client.chat(self.message, self.history)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class MainWindow(QMainWindow):
    """ZiTTA 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZiTTA 🧠✨ - 개인 AI 비서")
        self.setGeometry(100, 100, 1200, 800)
        
        # 모듈 초기화
        try:
            self.llm_client = LLMClient()
        except ValueError as e:
            QMessageBox.critical(self, "오류", str(e))
            sys.exit(1)
        
        self.todo_manager = TodoManager()
        self.memo_manager = MemoManager()
        self.file_explorer = FileExplorer()
        self.voice_handler = VoiceHandler()
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins()
        self.command_router = CommandRouter()
        
        self.conversation_history = []
        self.current_directory = os.getcwd()
        
        # UI 초기화
        self._init_ui()
        self._load_todos()
        self._load_memos()
    
    def _init_ui(self):
        """UI 초기화"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 탭 위젯 생성
        self.tabs = QTabWidget()
        
        # 탭 1: 대화 및 할 일
        self._init_chat_tab()
        
        # 탭 2: 메모
        self._init_memo_tab()
        
        # 탭 3: 파일 탐색
        self._init_file_explorer_tab()
        
        main_layout.addWidget(self.tabs)
    
    def _init_chat_tab(self):
        """대화 및 할 일 탭 초기화"""
        chat_tab = QWidget()
        chat_layout = QHBoxLayout(chat_tab)
        
        # 좌측: 대화 영역
        chat_widget = QWidget()
        chat_widget_layout = QVBoxLayout(chat_widget)
        
        # 대화 표시 영역
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("맑은 고딕", 10))
        self.chat_display.append("🧠 <b>ZiTTA</b>: 안녕하세요! 저는 ZiTTA입니다. 무엇을 도와드릴까요?")
        
        # 입력 영역
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("메시지를 입력하세요... (Enter로 전송)")
        self.input_field.returnPressed.connect(self._send_message)
        
        self.send_button = QPushButton("전송")
        self.send_button.clicked.connect(self._send_message)
        
        # 음성 입력 버튼
        self.voice_button = QPushButton("🎤 음성")
        self.voice_button.clicked.connect(self._start_voice_input)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.voice_button)
        
        chat_widget_layout.addWidget(QLabel("💬 대화"))
        chat_widget_layout.addWidget(self.chat_display)
        chat_widget_layout.addLayout(input_layout)
        
        # 우측: 할 일 관리 영역
        todo_widget = QWidget()
        todo_layout = QVBoxLayout(todo_widget)
        
        todo_layout.addWidget(QLabel("📝 할 일 관리"))
        
        # 할 일 목록
        self.todo_list = QListWidget()
        todo_layout.addWidget(self.todo_list)
        
        # 할 일 추가 버튼
        todo_button_layout = QHBoxLayout()
        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("새 할 일 입력...")
        self.todo_input.returnPressed.connect(self._add_todo)
        
        self.add_todo_button = QPushButton("추가")
        self.add_todo_button.clicked.connect(self._add_todo)
        
        todo_button_layout.addWidget(self.todo_input)
        todo_button_layout.addWidget(self.add_todo_button)
        todo_layout.addLayout(todo_button_layout)
        
        # 할 일 삭제 버튼
        self.delete_todo_button = QPushButton("선택 항목 삭제")
        self.delete_todo_button.clicked.connect(self._delete_todo)
        todo_layout.addWidget(self.delete_todo_button)
        
        # 스플리터로 좌우 분할
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(chat_widget)
        splitter.addWidget(todo_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        chat_layout.addWidget(splitter)
        self.tabs.addTab(chat_tab, "💬 대화 & 할 일")
    
    def _init_memo_tab(self):
        """메모 탭 초기화"""
        memo_tab = QWidget()
        memo_layout = QVBoxLayout(memo_tab)
        
        memo_layout.addWidget(QLabel("📝 메모 관리"))
        
        # 메모 목록
        self.memo_list = QListWidget()
        self.memo_list.itemDoubleClicked.connect(self._edit_memo)
        memo_layout.addWidget(self.memo_list)
        
        # 메모 추가/검색 영역
        memo_input_layout = QHBoxLayout()
        self.memo_title_input = QLineEdit()
        self.memo_title_input.setPlaceholderText("메모 제목...")
        self.memo_content_input = QTextEdit()
        self.memo_content_input.setPlaceholderText("메모 내용...")
        self.memo_tags_input = QLineEdit()
        self.memo_tags_input.setPlaceholderText("태그 (쉼표로 구분)...")
        
        memo_input_layout.addWidget(QLabel("제목:"))
        memo_input_layout.addWidget(self.memo_title_input)
        memo_input_layout.addWidget(QLabel("태그:"))
        memo_input_layout.addWidget(self.memo_tags_input)
        
        memo_button_layout = QHBoxLayout()
        self.add_memo_button = QPushButton("메모 추가")
        self.add_memo_button.clicked.connect(self._add_memo)
        self.search_memo_button = QPushButton("검색")
        self.search_memo_button.clicked.connect(self._search_memos)
        self.delete_memo_button = QPushButton("선택 메모 삭제")
        self.delete_memo_button.clicked.connect(self._delete_memo)
        
        memo_button_layout.addWidget(self.add_memo_button)
        memo_button_layout.addWidget(self.search_memo_button)
        memo_button_layout.addWidget(self.delete_memo_button)
        
        memo_layout.addLayout(memo_input_layout)
        memo_layout.addWidget(QLabel("내용:"))
        memo_layout.addWidget(self.memo_content_input)
        memo_layout.addLayout(memo_button_layout)
        
        self.tabs.addTab(memo_tab, "📝 메모")
    
    def _init_file_explorer_tab(self):
        """파일 탐색 탭 초기화"""
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)
        
        # 경로 표시 및 탐색 버튼
        path_layout = QHBoxLayout()
        self.path_label = QLabel(f"경로: {self.current_directory}")
        self.browse_button = QPushButton("폴더 선택")
        self.browse_button.clicked.connect(self._browse_directory)
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.clicked.connect(self._refresh_file_list)
        
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.browse_button)
        path_layout.addWidget(self.refresh_button)
        
        # 파일 목록
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self._open_file_item)
        file_layout.addLayout(path_layout)
        file_layout.addWidget(QLabel("📁 파일 목록"))
        file_layout.addWidget(self.file_list)
        
        # 파일 작업 버튼
        file_button_layout = QHBoxLayout()
        self.open_file_button = QPushButton("파일 열기")
        self.open_file_button.clicked.connect(self._open_selected_file)
        self.open_dir_button = QPushButton("폴더 열기")
        self.open_dir_button.clicked.connect(self._open_selected_directory)
        
        file_button_layout.addWidget(self.open_file_button)
        file_button_layout.addWidget(self.open_dir_button)
        file_layout.addLayout(file_button_layout)
        
        self._refresh_file_list()
        self.tabs.addTab(file_tab, "📁 파일 탐색")
    
    def _send_message(self):
        """메시지 전송"""
        message = self.input_field.text().strip()
        if not message:
            return
        
        # 사용자 메시지 표시
        self.chat_display.append(f"<b>사용자</b>: {message}")
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        
        # 플러그인 명령 처리 먼저 시도
        plugin_result = self.plugin_manager.handle_command(message)
        if plugin_result:
            self.chat_display.append(f"🔌 <b>플러그인 ({plugin_result.get('plugin', 'Unknown')})</b>: {plugin_result.get('response', '')}")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
            return
        
        # 명령 라우팅
        routed = self.command_router.route(message)
        
        if routed.type == "todo":
            # 할 일 관련 명령 처리
            if routed.action == "create":
                # LLM이 할 일을 추출하도록 요청
                todo_prompt = f"다음 명령에서 할 일 제목을 추출해주세요. 제목만 간단히 답변하세요: {message}"
                self._process_llm_response(todo_prompt, is_todo_extraction=True)
            else:
                todos = self.todo_manager.get_todos(completed=False)
                if todos:
                    todo_list = "\n".join([f"- {todo['title']}" for todo in todos])
                    response = f"현재 할 일 목록:\n{todo_list}"
                    self.chat_display.append(f"🧠 <b>ZiTTA</b>: {response}")
                else:
                    self.chat_display.append("🧠 <b>ZiTTA</b>: 할 일이 없습니다.")
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
        elif routed.type == "memo":
            # 메모 관련 명령 처리
            if routed.action == "create":
                memo_prompt = f"다음 명령에서 메모 제목을 추출해주세요. 제목만 간단히 답변하세요: {message}"
                self._process_llm_response(memo_prompt, is_memo_extraction=True)
            else:
                memos = self.memo_manager.get_memos()
                if memos:
                    memo_list = "\n".join([f"- {memo['title']}" for memo in memos[:10]])
                    response = f"현재 메모 목록 (최근 10개):\n{memo_list}"
                    self.chat_display.append(f"🧠 <b>ZiTTA</b>: {response}")
                else:
                    self.chat_display.append("🧠 <b>ZiTTA</b>: 메모가 없습니다.")
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
        elif routed.type == "file":
            # 파일 관련 명령 처리
            items = self.file_explorer.list_directory(self.current_directory)
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
                    response = f"현재 디렉토리 ({self.current_directory}) 내용 ({filter_text}):\n{file_list}"
                    self.chat_display.append(f"🧠 <b>ZiTTA</b>: {response}")
                else:
                    filter_text = "폴더" if filter_type == "dir" else "파일" if filter_type == "file" else "항목"
                    self.chat_display.append(f"🧠 <b>ZiTTA</b>: {filter_text}이(가) 없습니다.")
            else:
                self.chat_display.append("🧠 <b>ZiTTA</b>: 파일이 없습니다.")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
        else:
            # 일반 대화 (LLM fallback)
            self._process_llm_response(message)
    
    def _process_llm_response(self, message: str, is_todo_extraction: bool = False, is_memo_extraction: bool = False):
        """LLM 응답 처리 (비동기)"""
        self.worker = LLMWorker(self.llm_client, message, self.conversation_history)
        
        if is_todo_extraction:
            def handle_todo_response(response):
                # 할 일 추가
                todo_title = response.strip()
                if todo_title:
                    self.todo_manager.add_todo(todo_title)
                    self._load_todos()
                    self.chat_display.append(f"🧠 <b>ZiTTA</b>: 할 일 '{todo_title}'을 추가했습니다.")
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
            
            self.worker.response_ready.connect(handle_todo_response)
        elif is_memo_extraction:
            def handle_memo_response(response):
                # 메모 추가
                memo_title = response.strip()
                if memo_title:
                    self.memo_manager.add_memo(memo_title)
                    self._load_memos()
                    self.chat_display.append(f"🧠 <b>ZiTTA</b>: 메모 '{memo_title}'을 추가했습니다.")
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
            
            self.worker.response_ready.connect(handle_memo_response)
        else:
            def handle_response(response):
                # append()는 HTML을 지원하므로 HTML이 포함된 경우 그대로 전달
                self.chat_display.append(f"🧠 <b>ZiTTA</b>: {response}")
                # 대화 기록 업데이트
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": response})
                # 최근 20개만 유지
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
            
            self.worker.response_ready.connect(handle_response)
        
        self.worker.error_occurred.connect(lambda e: self._handle_error(e))
        self.worker.start()
    
    def _handle_error(self, error_msg):
        """오류 처리"""
        self.chat_display.append(f"❌ <b>오류</b>: {error_msg}")
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
    
    def _load_todos(self):
        """할 일 목록 로드"""
        self.todo_list.clear()
        todos = self.todo_manager.get_todos(completed=False)
        
        for todo in todos:
            item_text = f"[{todo['id']}] {todo['title']}"
            if todo['description']:
                item_text += f"\n  {todo['description']}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, todo['id'])
            self.todo_list.addItem(item)
    
    def _add_todo(self):
        """할 일 추가"""
        title = self.todo_input.text().strip()
        if not title:
            return
        
        self.todo_manager.add_todo(title)
        self.todo_input.clear()
        self._load_todos()
    
    def _delete_todo(self):
        """선택된 할 일 삭제"""
        current_item = self.todo_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "알림", "삭제할 항목을 선택하세요.")
            return
        
        todo_id = current_item.data(Qt.ItemDataRole.UserRole)
        if self.todo_manager.delete_todo(todo_id):
            self._load_todos()
            QMessageBox.information(self, "성공", "할 일이 삭제되었습니다.")
        else:
            QMessageBox.warning(self, "오류", "할 일 삭제에 실패했습니다.")
    
    def _start_voice_input(self):
        """음성 입력 시작"""
        QMessageBox.information(self, "음성 입력", "음성 입력 기능은 준비 중입니다.\n음성 파일을 선택하거나 마이크 입력을 지원합니다.")
        # TODO: 실제 음성 입력 구현
    
    def _load_memos(self):
        """메모 목록 로드"""
        self.memo_list.clear()
        memos = self.memo_manager.get_memos()
        
        for memo in memos:
            item_text = f"[{memo['id']}] {memo['title']}"
            if memo['tags']:
                item_text += f" (태그: {memo['tags']})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, memo['id'])
            self.memo_list.addItem(item)
    
    def _add_memo(self):
        """메모 추가"""
        title = self.memo_title_input.text().strip()
        content = self.memo_content_input.toPlainText().strip()
        tags = self.memo_tags_input.text().strip()
        
        if not title:
            QMessageBox.warning(self, "알림", "메모 제목을 입력하세요.")
            return
        
        self.memo_manager.add_memo(title, content, tags)
        self.memo_title_input.clear()
        self.memo_content_input.clear()
        self.memo_tags_input.clear()
        self._load_memos()
        QMessageBox.information(self, "성공", "메모가 추가되었습니다.")
    
    def _edit_memo(self, item):
        """메모 편집"""
        memo_id = item.data(Qt.ItemDataRole.UserRole)
        memo = self.memo_manager.get_memo(memo_id)
        
        if memo:
            self.memo_title_input.setText(memo['title'])
            self.memo_content_input.setPlainText(memo.get('content', ''))
            self.memo_tags_input.setText(memo.get('tags', ''))
            
            # 편집 모드로 전환
            self.add_memo_button.setText("메모 수정")
            self.add_memo_button.clicked.disconnect()
            self.add_memo_button.clicked.connect(lambda: self._update_memo(memo_id))
    
    def _update_memo(self, memo_id):
        """메모 수정"""
        title = self.memo_title_input.text().strip()
        content = self.memo_content_input.toPlainText().strip()
        tags = self.memo_tags_input.text().strip()
        
        if self.memo_manager.update_memo(memo_id, title, content, tags):
            self._load_memos()
            self.memo_title_input.clear()
            self.memo_content_input.clear()
            self.memo_tags_input.clear()
            self.add_memo_button.setText("메모 추가")
            self.add_memo_button.clicked.disconnect()
            self.add_memo_button.clicked.connect(self._add_memo)
            QMessageBox.information(self, "성공", "메모가 수정되었습니다.")
    
    def _search_memos(self):
        """메모 검색"""
        query = self.memo_title_input.text().strip()
        self.memo_list.clear()
        memos = self.memo_manager.get_memos(search_query=query if query else None)
        
        for memo in memos:
            item_text = f"[{memo['id']}] {memo['title']}"
            if memo['tags']:
                item_text += f" (태그: {memo['tags']})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, memo['id'])
            self.memo_list.addItem(item)
    
    def _delete_memo(self):
        """선택된 메모 삭제"""
        current_item = self.memo_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "알림", "삭제할 메모를 선택하세요.")
            return
        
        memo_id = current_item.data(Qt.ItemDataRole.UserRole)
        if self.memo_manager.delete_memo(memo_id):
            self._load_memos()
            QMessageBox.information(self, "성공", "메모가 삭제되었습니다.")
        else:
            QMessageBox.warning(self, "오류", "메모 삭제에 실패했습니다.")
    
    def _browse_directory(self):
        """디렉토리 선택"""
        directory = QFileDialog.getExistingDirectory(self, "폴더 선택", self.current_directory)
        if directory:
            self.current_directory = directory
            self.path_label.setText(f"경로: {self.current_directory}")
            self._refresh_file_list()
    
    def _refresh_file_list(self):
        """파일 목록 새로고침"""
        self.file_list.clear()
        items = self.file_explorer.list_directory(self.current_directory)
        
        for item in items:
            icon = "📁" if item["is_directory"] else "📄"
            size_text = f" ({self._format_size(item['size'])})" if not item["is_directory"] else ""
            item_text = f"{icon} {item['name']}{size_text}"
            
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.file_list.addItem(list_item)
    
    def _format_size(self, size: int) -> str:
        """파일 크기 포맷팅"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _open_file_item(self, item):
        """파일/디렉토리 더블클릭 처리"""
        file_data = item.data(Qt.ItemDataRole.UserRole)
        if file_data["is_directory"]:
            self.current_directory = file_data["path"]
            self.path_label.setText(f"경로: {self.current_directory}")
            self._refresh_file_list()
        else:
            self._open_file(file_data["path"])
    
    def _open_selected_file(self):
        """선택된 파일 열기"""
        current_item = self.file_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "알림", "열 파일을 선택하세요.")
            return
        
        file_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not file_data["is_directory"]:
            self._open_file(file_data["path"])
        else:
            QMessageBox.warning(self, "알림", "파일을 선택하세요.")
    
    def _open_file(self, file_path: str):
        """파일 열기"""
        if self.file_explorer.open_file(file_path):
            self.chat_display.append(f"📁 파일 열기: {file_path}")
        else:
            QMessageBox.warning(self, "오류", "파일을 열 수 없습니다.")
    
    def _open_selected_directory(self):
        """선택된 디렉토리 열기"""
        current_item = self.file_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "알림", "열 폴더를 선택하세요.")
            return
        
        file_data = current_item.data(Qt.ItemDataRole.UserRole)
        if file_data["is_directory"]:
            if self.file_explorer.open_directory(file_data["path"]):
                self.chat_display.append(f"📁 폴더 열기: {file_data['path']}")
        else:
            QMessageBox.warning(self, "알림", "폴더를 선택하세요.")


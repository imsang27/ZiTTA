"""
ZiTTA 메인 GUI 창
PyQt6를 사용하여 구현된 메인 인터페이스
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QMessageBox, QTabWidget, QFileDialog, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
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
from core.engine import ZiTTAEngine

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
        
        # ZiTTA 엔진 초기화 (기존 모듈들을 주입)
        self.engine = ZiTTAEngine(
            command_router=self.command_router,
            plugin_manager=self.plugin_manager,
            todo_manager=self.todo_manager,
            memo_manager=self.memo_manager,
            file_explorer=self.file_explorer,
            llm_client=self.llm_client
        )
        
        self.conversation_history = []
        self.current_directory = os.getcwd()
        self.current_state = "idle"  # 애니메이션 상태: idle, wake, think, resolve
        
        # UI 초기화
        self._init_ui()
        self._load_todos()
        self._load_memos()
    
    def _init_ui(self):
        """UI 초기화"""
        # 배경 애니메이션을 위한 스택 위젯
        stack = QStackedWidget()
        self.setCentralWidget(stack)
        
        # 배경 애니메이션 (레이어 0)
        self.animation_view = QWebEngineView()
        glow_path = os.path.join(os.path.dirname(__file__), "glow.html")
        if os.path.exists(glow_path):
            file_url = QUrl.fromLocalFile(os.path.abspath(glow_path))
            self.animation_view.load(file_url)
        else:
            # glow.html이 없으면 빈 위젯
            no_animation = QWidget()
            no_animation.setStyleSheet("background: #0B0E14;")
            self.animation_view = no_animation
        stack.addWidget(self.animation_view)
        
        # 메인 콘텐츠 (레이어 1)
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 탭 위젯 생성
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background: rgba(11, 14, 20, 0.85);
                border: none;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.8);
                padding: 8px 16px;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 0.2);
                color: rgba(255, 255, 255, 1.0);
            }
        """)
        
        # 탭 1: 대화 및 할 일
        self._init_chat_tab()
        
        # 탭 2: 메모
        self._init_memo_tab()
        
        # 탭 3: 파일 탐색
        self._init_file_explorer_tab()
        
        main_layout.addWidget(self.tabs)
        stack.addWidget(content_widget)
        
        # 콘텐츠 레이어를 위로
        stack.setCurrentIndex(1)
    
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
        
        # 상태 변경: wake (입력 시작)
        self._set_animation_state("wake")
        
        # 사용자 메시지 표시
        self.chat_display.append(f"<b>사용자</b>: {message}")
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        
        # 엔진을 통해 메시지 처리
        result = self.engine.handle(message, self.current_directory)
        
        # 결과에 따라 처리
        if result["type"] == "plugin":
            # 플러그인 응답
            self.chat_display.append(f"🔌 <b>플러그인 ({result.get('plugin_name', 'Unknown')})</b>: {result.get('response', '')}")
            self._set_animation_state("resolve")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
        elif result["needs_llm"]:
            # LLM 처리가 필요한 경우 (todo/memo create 또는 일반 대화)
            # 상태 변경: think (처리 중)
            self._set_animation_state("think")
            if result["type"] in ["todo", "memo"]:
                # todo/memo 생성 시 LLM으로 제목 추출
                self._process_llm_response(
                    result["llm_prompt"],
                    result_type=result["type"],
                    action=result["action"]
                )
            else:
                # 일반 대화
                self._process_llm_response(result["llm_prompt"])
        else:
            # 즉시 응답 가능한 경우 (todo/memo/file list)
            self.chat_display.append(f"🧠 <b>ZiTTA</b>: {result.get('response', '')}")
            self._set_animation_state("resolve")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
    
    def _process_llm_response(self, message: str, result_type: str = None, action: str = None):
        """LLM 응답 처리 (비동기)"""
        self.worker = LLMWorker(self.llm_client, message, self.conversation_history)
        
        if result_type in ["todo", "memo"] and action == "create":
            # todo/memo 생성 시 엔진을 통해 처리
            def handle_create_response(response):
                final_result = self.engine.process_llm_response(response, result_type, action)
                self.chat_display.append(f"🧠 <b>ZiTTA</b>: {final_result.get('response', '')}")
                # UI 업데이트
                if result_type == "todo":
                    self._load_todos()
                elif result_type == "memo":
                    self._load_memos()
                self._set_animation_state("resolve")
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
            
            self.worker.response_ready.connect(handle_create_response)
        else:
            # 일반 대화
            def handle_response(response):
                # append()는 HTML을 지원하므로 HTML이 포함된 경우 그대로 전달
                self.chat_display.append(f"🧠 <b>ZiTTA</b>: {response}")
                # 대화 기록 업데이트
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": response})
                # 최근 20개만 유지
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                self._set_animation_state("resolve")
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
            
            self.worker.response_ready.connect(handle_response)
        
        self.worker.error_occurred.connect(lambda e: self._handle_error(e))
        self.worker.start()
    
    def _handle_error(self, error_msg):
        """오류 처리"""
        self.chat_display.append(f"❌ <b>오류</b>: {error_msg}")
        self._set_animation_state("resolve")
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
    
    def _set_animation_state(self, state: str):
        """애니메이션 상태 설정"""
        if state in ["idle", "wake", "think", "resolve"]:
            self.current_state = state
            if hasattr(self, 'animation_view') and isinstance(self.animation_view, QWebEngineView):
                # JavaScript 함수 호출
                js_code = f"window.setAnimationState('{state}');"
                self.animation_view.page().runJavaScript(js_code)
    
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


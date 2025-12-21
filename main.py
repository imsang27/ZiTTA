"""
ZiTTA 메인 실행 파일
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# GUI 모듈 import
from gui.main_window import MainWindow
from core.config import Config

def main():
    """메인 함수"""
    # 설정 검증
    try:
        Config.validate()
    except ValueError as e:
        print(f"설정 오류: {e}")
        print("설정 방법:")
        print("1. .env.example 파일을 .env로 복사하세요")
        print("2. .env 파일에 OPENAI_API_KEY를 설정하세요")
        sys.exit(1)
    
    # PyQt 애플리케이션 초기화
    app = QApplication(sys.argv)
    app.setApplicationName(Config.APP_NAME)
    app.setApplicationVersion(Config.APP_VERSION)
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 이벤트 루프 실행
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


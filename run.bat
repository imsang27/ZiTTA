@echo off
chcp 65001 >nul 2>&1
REM 가상환경에서 프로그램 실행 스크립트

REM 스크립트가 있는 디렉토리로 이동
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 생성되지 않았습니다.
    echo 먼저 setup_venv.bat을 실행해주세요.
    echo 현재 디렉토리: %CD%
    pause
    exit /b 1
)

echo 가상환경 활성화 및 프로그램 실행 중...
call venv\Scripts\activate.bat
python main.py

REM 프로그램 종료 후 가상환경 비활성화
deactivate

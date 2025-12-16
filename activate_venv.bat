@echo off
chcp 65001 >nul 2>&1
REM 가상환경 활성화 스크립트

REM 스크립트가 있는 디렉토리로 이동
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 생성되지 않았습니다.
    echo 먼저 setup_venv.bat을 실행해주세요.
    echo 현재 디렉토리: %CD%
    pause
    exit /b 1
)

echo 가상환경 활성화 중...
call venv\Scripts\activate.bat

echo.
echo ========================================
echo 가상환경이 활성화되었습니다!
echo ========================================
echo.
echo 이제 다음 명령으로 프로그램을 실행할 수 있습니다:
echo   python main.py
echo.
echo 가상환경을 비활성화하려면 'deactivate'를 입력하세요.
echo.

cmd /k

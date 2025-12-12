@echo off
chcp 65001 >nul 2>&1
REM 스크립트가 있는 디렉토리로 이동
cd /d "%~dp0"

echo ========================================
echo ZiTTA 가상환경 설정 스크립트
echo ========================================
echo.

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

echo [1/3] Python 버전 확인 중...
python --version
echo.

REM 가상환경이 이미 존재하는지 확인
if exist "venv\" (
    echo [경고] venv 폴더가 이미 존재합니다.
    set /p choice="기존 가상환경을 삭제하고 새로 만들까요? (y/n): "
    if /i "%choice%"=="y" (
        echo 기존 가상환경 삭제 중...
        rmdir /s /q venv
    ) else (
        echo 기존 가상환경을 사용합니다.
        goto :install
    )
)

echo [2/3] 가상환경 생성 중...
python -m venv venv
if errorlevel 1 (
    echo [오류] 가상환경 생성에 실패했습니다.
    pause
    exit /b 1
)
echo 가상환경이 성공적으로 생성되었습니다.
echo.

:install
echo [3/3] 패키지 설치 중...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [오류] 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 가상환경 설정이 완료되었습니다!
echo ========================================
echo.
echo 가상환경을 활성화하려면 다음 명령을 실행하세요:
echo   activate_venv.bat
echo.
echo 또는 직접 실행:
echo   venv\Scripts\activate.bat
echo.
pause

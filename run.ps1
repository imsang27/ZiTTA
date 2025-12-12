# 가상환경에서 프로그램 실행 스크립트 (PowerShell)

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[오류] 가상환경이 생성되지 않았습니다." -ForegroundColor Red
    Write-Host "먼저 setup_venv.ps1을 실행해주세요." -ForegroundColor Red
    Read-Host "아무 키나 눌러 종료"
    exit 1
}

Write-Host "가상환경 활성화 및 프로그램 실행 중..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"
python main.py

# 프로그램 종료 후 가상환경 비활성화
deactivate


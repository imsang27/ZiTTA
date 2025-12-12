# 가상환경 활성화 스크립트 (PowerShell)

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[오류] 가상환경이 생성되지 않았습니다." -ForegroundColor Red
    Write-Host "먼저 setup_venv.ps1을 실행해주세요." -ForegroundColor Red
    Read-Host "아무 키나 눌러 종료"
    exit 1
}

Write-Host "가상환경 활성화 중..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "가상환경이 활성화되었습니다!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "이제 다음 명령으로 프로그램을 실행할 수 있습니다:" -ForegroundColor Yellow
Write-Host "  python main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "가상환경을 비활성화하려면 'deactivate'를 입력하세요." -ForegroundColor Yellow
Write-Host ""


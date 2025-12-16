# ZiTTA 가상환경 설정 스크립트 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ZiTTA 가상환경 설정 스크립트" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Python이 설치되어 있는지 확인
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/3] Python 버전 확인 중..." -ForegroundColor Green
    Write-Host $pythonVersion
    Write-Host ""
} catch {
    Write-Host "[오류] Python이 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "Python 3.8 이상을 설치해주세요." -ForegroundColor Red
    Read-Host "아무 키나 눌러 종료"
    exit 1
}

# 가상환경이 이미 존재하는지 확인
if (Test-Path "venv") {
    Write-Host "[경고] venv 폴더가 이미 존재합니다." -ForegroundColor Yellow
    $choice = Read-Host "기존 가상환경을 삭제하고 새로 만들까요? (y/n)"
    if ($choice -eq "y" -or $choice -eq "Y") {
        Write-Host "기존 가상환경 삭제 중..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
    } else {
        Write-Host "기존 가상환경을 사용합니다." -ForegroundColor Green
        $skipCreate = $true
    }
}

if (-not $skipCreate) {
    Write-Host "[2/3] 가상환경 생성 중..." -ForegroundColor Green
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[오류] 가상환경 생성에 실패했습니다." -ForegroundColor Red
        Read-Host "아무 키나 눌러 종료"
        exit 1
    }
    Write-Host "가상환경이 성공적으로 생성되었습니다." -ForegroundColor Green
    Write-Host ""
}

Write-Host "[3/3] 패키지 설치 중..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[오류] 패키지 설치에 실패했습니다." -ForegroundColor Red
    Read-Host "아무 키나 눌러 종료"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "가상환경 설정이 완료되었습니다!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "가상환경을 활성화하려면 다음 명령을 실행하세요:" -ForegroundColor Yellow
Write-Host "  .\activate_venv.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "또는 직접 실행:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Read-Host "아무 키나 눌러 종료"


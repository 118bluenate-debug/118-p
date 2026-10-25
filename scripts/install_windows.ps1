# ==============================================================================
# 118 팔배개 (118 PAL-BEGAE) - Windows 11 환경 자동 설치 스크립트
# 한국인터넷진흥원(KISA) 118 AI 상담지원 시스템
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [118 팔배개] Windows 11 + RTX 5080 환경 설치 시작" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$WorkspaceRoot = "c:\118-p"
$PythonExe = "C:\Users\ccc\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}

Write-Host "[1/4] Python 3.11 환경 점검..." -ForegroundColor Yellow
if (-not $PythonExe) {
    Write-Host "Python 3.11이 감지되지 않았습니다. 설치를 진행합니다..." -ForegroundColor Yellow
    winget install --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements --override "/passive InstallAllUsers=0 Include_launcher=0 Include_pip=1 PrependPath=1"
}
Write-Host "Python 경로: $PythonExe" -ForegroundColor Green

Write-Host "[2/4] Python 필수 의존성 패키지 설치..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r "$WorkspaceRoot\requirements.txt"

Write-Host "[3/4] 작업 디렉터리 생성..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$WorkspaceRoot\data\crm_records" | Out-Null
New-Item -ItemType Directory -Force -Path "$WorkspaceRoot\data\whisper_models" | Out-Null

Write-Host "[4/4] Ollama 서비스 및 모델 확인..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
    Write-Host "Ollama 서비스 온라인 확인 완료. 설치된 모델: $($ollamaCheck.models.name -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "경고: Ollama 서비스가 응답하지 않습니다. 백그라운드에서 Ollama를 실행해 주세요." -ForegroundColor Yellow
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [118 팔배개] 설치가 성공적으로 완료되었습니다!" -ForegroundColor Green
Write-Host " 서버 실행: powershell scripts\run_server.ps1" -ForegroundColor White
Write-Host " 오디오 캡처: powershell scripts\run_agent.ps1" -ForegroundColor White
Write-Host " 웹 대시보드: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

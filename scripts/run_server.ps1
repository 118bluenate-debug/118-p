# ==============================================================================
# 118 팔배개 (118 PAL-BEGAE) - FastAPI 서버 실행 스크립트
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PythonExe = "C:\Users\ccc\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python).Source
}

Set-Location "c:\118-p"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [118 팔배개] STT & Ollama 상담지원 서버 기동" -ForegroundColor Cyan
Write-Host " 웹 대시보드 URL: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host " 종료하려면 Ctrl + C 를 누르세요." -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan

& $PythonExe -m uvicorn server.main:app --host 0.0.0.0 --port 8000

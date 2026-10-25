# ==============================================================================
# 118 팔배개 (118 PAL-BEGAE) - Windows Line-in 오디오 수집 에이전트 실행
# ==============================================================================

param (
    [int]$Device = -1,
    [switch]$ListDevices,
    [switch]$TestVad
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PythonExe = "C:\Users\ccc\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python).Source
}

Set-Location "c:\118-p"

if ($ListDevices) {
    & $PythonExe audio_agent\run_agent.py --list-devices
    exit
}

if ($TestVad) {
    if ($Device -ge 0) {
        & $PythonExe audio_agent\run_agent.py --test-vad --device $Device
    } else {
        & $PythonExe audio_agent\run_agent.py --test-vad
    }
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [118 팔배개] Windows Line-in 오디오 캡처 에이전트 기동" -ForegroundColor Cyan
Write-Host " 대상 서버: ws://127.0.0.1:8000/ws/audio" -ForegroundColor Green
Write-Host " 종료하려면 Ctrl + C 를 누르세요." -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan

if ($Device -ge 0) {
    & $PythonExe audio_agent\run_agent.py --device $Device
} else {
    & $PythonExe audio_agent\run_agent.py
}

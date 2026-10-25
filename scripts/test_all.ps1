# ==============================================================================
# 118 팔배개 (118 PAL-BEGAE) - 전체 단위 및 통합 테스트 실행기
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

$PythonExe = "C:\Users\ccc\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python).Source
}

Set-Location "c:\118-p"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [118 팔배개] 전체 시스템 단위 및 통합 테스트 시작" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$Tests = @(
    "tests\test_pii_and_terms.py",
    "tests\test_vad.py",
    "tests\test_mock_crm.py",
    "tests\test_server_init.py",
    "tests\test_ollama.py"
)

$Passed = 0
$Failed = 0

foreach ($t in $Tests) {
    Write-Host ""
    Write-Host ">>> 테스트 실행: $t" -ForegroundColor Yellow
    & $PythonExe $t
    if ($LASTEXITCODE -eq 0) {
        Write-Host " 결과: [성공 PASS]" -ForegroundColor Green
        $Passed++
    } else {
        Write-Host " 결과: [실패 FAIL]" -ForegroundColor Red
        $Failed++
    }
}

$statusColor = if ($Failed -eq 0) { "Green" } else { "Red" }
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [테스트 완료 보고] 성공: $Passed 건 | 실패: $Failed 건" -ForegroundColor $statusColor
Write-Host "============================================================" -ForegroundColor Cyan

if ($Failed -gt 0) {
    exit 1
}

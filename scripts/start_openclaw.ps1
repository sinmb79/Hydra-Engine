# HYDRA — OpenClaw 게이트웨이 + 브리지 시작 스크립트
# 실행: PowerShell에서 .\scripts\start_openclaw.ps1

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot

Write-Host "[1/2] OpenClaw 게이트웨이 시작..." -ForegroundColor Cyan
Start-Process -NoNewWindow -FilePath "openclaw" -ArgumentList "gateway", "--port", "18789", "--force", "--auth", "token" -PassThru | Out-Null
Start-Sleep -Seconds 3

# 게이트웨이 헬스체크
try {
    $health = openclaw health 2>&1
    Write-Host "[1/2] 게이트웨이 정상: $health" -ForegroundColor Green
} catch {
    Write-Host "[1/2] 게이트웨이 응답 없음, 계속 진행..." -ForegroundColor Yellow
}

Write-Host "[2/2] OpenClaw 브리지 시작..." -ForegroundColor Cyan
Set-Location $ProjectDir

$env:REDIS_URL = "redis://127.0.0.1:6379"
$env:OPENCLAW_AGENT_ID = "main"
$env:OPENCLAW_POLL_INTERVAL = "300"

python -m hydra.agent.openclaw_bridge

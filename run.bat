@echo off
setlocal enabledelayedexpansion
title AgentX — Autonomous AI Teammates

echo ========================================
echo         AGENTX LOCAL DEVELOPMENT
echo ========================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH.
    pause
    exit /b 1
)

:: 2. Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not found in PATH.
    pause
    exit /b 1
)

:: ========================================
:: [1/4] CHECK N8N (Port 32768)
:: ========================================
echo [1/4] Checking n8n...

set N8N_URL=http://localhost:32768
set N8N_RUNNING=0

powershell -Command "$r = try { (Invoke-WebRequest -Uri '%N8N_URL%/healthz' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { try { (Invoke-WebRequest -Uri '%N8N_URL%' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 } }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    set N8N_RUNNING=1
) else (
    echo [AgentX] n8n is NOT reachable at %N8N_URL%
    echo [AgentX] Attempting to start n8n...
    
    docker start n8n >nul 2>&1
    if !errorlevel! neq 0 docker start agentx-n8n >nul 2>&1
    if !errorlevel! neq 0 docker run -d --name agentx-n8n -p 32768:5678 n8nio/n8n >nul 2>&1
    
    :: Wait up to 10 seconds for n8n to respond
    echo       Waiting for n8n to start...
    for /l %%i in (1,1,10) do (
        powershell -Command "$r = try { (Invoke-WebRequest -Uri '%N8N_URL%' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
        if !errorlevel! equ 0 (
            set N8N_RUNNING=1
            goto :n8n_done
        )
        timeout /t 1 /nobreak >nul
    )
)

:n8n_done
if %N8N_RUNNING% equ 1 (
    echo       n8n: RUNNING
) else (
    echo       n8n: UNREACHABLE (Proceeding with local dev mode)
)
echo.

:: ========================================
:: [2/4] START FASTAPI BACKEND
:: ========================================
echo [2/4] Checking AgentX backend...
powershell -Command "$r = try { (Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    start "AgentX Backend (FastAPI)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    
    :: Wait for FastAPI health
    for /l %%i in (1,1,15) do (
        powershell -Command "$r = try { (Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
        if !errorlevel! equ 0 goto :backend_ready
        timeout /t 1 /nobreak >nul
    )
)
:backend_ready
echo       FastAPI: RUNNING
echo.

:: ========================================
:: [3/4] START REACT FRONTEND
:: ========================================
echo [3/4] Checking React frontend...
powershell -Command "$r = try { (Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    start "AgentX Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev"
    
    :: Wait for React frontend port 3000
    for /l %%i in (1,1,15) do (
        powershell -Command "$r = try { (Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
        if !errorlevel! equ 0 goto :frontend_ready
        timeout /t 1 /nobreak >nul
    )
)
:frontend_ready
echo       Frontend: RUNNING
echo.

:: ========================================
:: [4/4] TEST AGENTX → N8N CONNECTIVITY
:: ========================================
echo [4/4] Testing n8n connectivity...
powershell -Command "$res = try { (Invoke-RestMethod -Uri 'http://localhost:8000/health/n8n' -TimeoutSec 3).status } catch { 'error' }; if ($res -eq 'ok') { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo       AgentX -^> n8n: PASS
) else (
    echo       AgentX -^> n8n: WARNING (n8n offline or unconfigured)
)
echo.

:: ========================================
:: FINAL STATUS & BROWSER LAUNCH
:: ========================================
echo ========================================
echo AgentX is ready.
echo ========================================
echo.
echo URLs:
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo n8n:      http://localhost:32768
echo.

:: Open browser after services are ready
start http://localhost:3000

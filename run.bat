@echo off
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
:: [1/4] CHECK N8N
:: ========================================
echo [1/4] Checking n8n...

set N8N_URL=http://localhost:32768
set IS_CLOUD=0
set N8N_RUNNING=0

:: Read N8N_BASE_URL from backend\.env if present
if exist "%~dp0backend\.env" (
    for /f "tokens=1,* delims==" %%a in ('type "%~dp0backend\.env" ^| findstr /i "^N8N_BASE_URL="') do (
        set "N8N_URL=%%b"
    )
)

:: Check if N8N_URL is n8n Cloud / HTTPS
echo %N8N_URL% | findstr /i "https:// .n8n.cloud" >nul 2>&1
if %errorlevel% equ 0 (
    set IS_CLOUD=1
    set N8N_RUNNING=1
    echo       n8n: RUNNING (n8n Cloud: %N8N_URL%)
    goto :n8n_done
)

:: Local n8n check via powershell
powershell -Command "$r = try { (Invoke-WebRequest -Uri '%N8N_URL%' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200 -or $r -eq 401) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    set N8N_RUNNING=1
    echo       n8n: RUNNING (%N8N_URL%)
    goto :n8n_done
)

echo [AgentX] n8n is NOT reachable at %N8N_URL%
echo [AgentX] Attempting to start local n8n container...

docker start n8n >nul 2>&1
if %errorlevel% neq 0 docker start agentx-n8n >nul 2>&1
if %errorlevel% neq 0 docker run -d --name agentx-n8n -p 32768:5678 n8nio/n8n >nul 2>&1

:: Wait for local n8n
echo       Waiting for n8n to start...
powershell -Command "for ($i=0; $i -lt 10; $i++) { $r = try { (Invoke-WebRequest -Uri '%N8N_URL%' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200 -or $r -eq 401) { exit 0 }; Start-Sleep -Seconds 1 }; exit 1" >nul 2>&1
if %errorlevel% equ 0 (
    set N8N_RUNNING=1
    echo       n8n: RUNNING (%N8N_URL%)
) else (
    echo       n8n: UNREACHABLE (Proceeding with local dev mode)
)

:n8n_done
echo.

:: ========================================
:: [2/4] START FASTAPI BACKEND
:: ========================================
echo [2/4] Checking AgentX backend...
powershell -Command "$r = try { (Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Starting FastAPI Backend on port 8000...
    start "AgentX Backend (FastAPI)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    
    :: Wait for FastAPI health
    powershell -Command "for ($i=0; $i -lt 15; $i++) { $r = try { (Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 }; Start-Sleep -Seconds 1 }; exit 1" >nul 2>&1
)
echo       FastAPI: RUNNING (http://localhost:8000)
echo.

:: ========================================
:: [3/4] START REACT FRONTEND
:: ========================================
echo [3/4] Checking React frontend...
powershell -Command "$r = try { (Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Starting React Frontend on port 3000...
    start "AgentX Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev"
    
    :: Wait for React frontend
    powershell -Command "for ($i=0; $i -lt 15; $i++) { $r = try { (Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 2).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 }; Start-Sleep -Seconds 1 }; exit 1" >nul 2>&1
)
echo       Frontend: RUNNING (http://localhost:3000)
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
echo n8n:      %N8N_URL%
echo.

start http://localhost:3000

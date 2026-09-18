@echo off
title AgentX — Autonomous AI Teammates
echo ===================================================
echo     AgentX — Autonomous AI Teammates for Business
echo ===================================================
echo.

:: Check python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH.
    pause
    exit /b 1
)

:: Check node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not found in PATH.
    pause
    exit /b 1
)

echo [1/2] Launching AgentX FastAPI Backend on port 8000...
start "AgentX Backend (FastAPI)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Launching AgentX React Frontend on port 3000...
start "AgentX Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===================================================
echo   AgentX is launching!
echo.
echo   - React Command Center: http://localhost:3000
echo   - FastAPI Backend API:  http://localhost:8000
echo   - Interactive API Docs: http://localhost:8000/docs
echo ===================================================
echo.

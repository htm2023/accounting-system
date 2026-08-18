@echo off
title Accounting System Launcher

echo Starting backend server...
start "Backend Server" cmd /k "cd /d C:\Users\Haytham\accounting-system\backend && venv\Scripts\python.exe manage.py runserver"

echo Starting frontend server...
start "Frontend Server" cmd /k "cd /d C:\Users\Haytham\accounting-system\frontend && npm run dev"

echo Waiting for servers to start...
timeout /t 6 /nobreak >nul

echo Opening browser...
start http://localhost:5173

exit

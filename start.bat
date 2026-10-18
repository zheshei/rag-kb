@echo off
chcp 65001 >nul
title RAG 知识库问答系统 - 启动器
echo ============================================
echo    RAG 企业级知识库问答系统 一键启动
echo ============================================
echo.

if not exist "%~dp0backend\.venv\Scripts\python.exe" (
    echo [错误] 未找到后端虚拟环境，请先执行：
    echo   cd backend ^&^& python -m venv .venv
    echo   .venv\Scripts\python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    pause
    exit /b 1
)

echo [1/3] 启动后端服务 (127.0.0.1:8000) ...
start "RAG-Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] 启动前端服务 (localhost:5173) ...
start "RAG-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 2 /nobreak >nul
echo [3/3] 完成！
echo.
echo 请用浏览器打开： http://localhost:5173
echo 管理员账号： admin / 123456
echo.
pause

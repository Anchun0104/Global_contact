@echo off
echo Starting professor database system...
echo Open http://localhost:8000 in browser after startup.
echo Default account: admin / admin123
echo.
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Startup failed. Please run install.bat first.
    pause
)

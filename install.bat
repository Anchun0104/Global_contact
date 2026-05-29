@echo off
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo Install complete!
) else (
    echo Install failed, please check network.
)
pause

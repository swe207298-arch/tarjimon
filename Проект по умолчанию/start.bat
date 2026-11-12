@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv" (
    echo [1/3] Virtual muhit yaratilmoqda...
    py -m venv .venv 2>nul || python -m venv .venv
)

if not exist ".env" (
    echo [!] .env fayli topilmadi. .env.example dan nusxa olib to'ldiring.
    pause
    exit /b 1
)

echo [2/3] Kutubxonalar tekshirilmoqda...
call ".venv\Scripts\activate.bat"
python -m pip install --disable-pip-version-check -q -r requirements.txt

if errorlevel 1 (
    echo [x] Kutubxonalarni o'rnatib bo'lmadi.
    pause
    exit /b 1
)

echo [3/3] Bot ishga tushirilmoqda...
python bot.py
pause

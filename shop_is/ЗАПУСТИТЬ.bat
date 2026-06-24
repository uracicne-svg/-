@echo off
setlocal enabledelayedexpansion
title ShopIS

cd /d "%~dp0"

echo.
echo  ShopIS - Avtozapusk
echo  ====================
echo.

echo [1/3] Proverka Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo OSHIBKA: Python ne nayden!
    echo Skaychay s https://python.org
    echo Pri ustanovke otmet' "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo.

echo [2/3] Ustanovka zavisimostey...
if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

pip install --no-user --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org Flask bcrypt -q --disable-pip-version-check
if errorlevel 1 (
    echo Pytayus' ustanovit' bez prокси...
    pip install --no-user Flask bcrypt --index-url https://pypi.org/simple/ -q
)

python -c "import flask, bcrypt" >nul 2>&1
if errorlevel 1 (
    echo.
    echo OSHIBKA: Ne udalos' ustanovit' pakety.
    echo Poprobuy zapustit' ot imeni administratora (PKM - Zapustit' kak administrator)
    echo.
    pause
    exit /b 1
)
echo Pakety ustanovleny.
echo.

echo [3/3] Zapusk...
echo.
echo  Adres: http://localhost:5000
echo  Login: admin
echo  Parol: admin123
echo  Ostanovit': Ctrl+C
echo.

start /min "" cmd /c "timeout /t 3 >nul && start http://localhost:5000"
python app.py

echo.
pause

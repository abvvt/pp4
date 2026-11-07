@echo off
cd /d "%~dp0"
echo === CVI-IA ===
where python >nul 2>nul
if errorlevel 1 (echo Instala Python 3.10 o superior y marca Add Python to PATH.& pause & exit /b 1)
if not exist ".venv\Scripts\python.exe" python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (echo Error instalando dependencias. Revisa internet.& pause & exit /b 1)
python -m streamlit run app.py
pause

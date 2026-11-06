@echo off
TITLE Clinica Veterinaria Amor Animal - FastAPI
echo ========================================================
echo   CLINICA VETERINARIA "AMOR ANIMAL"
echo   Iniciando Servidor Web FastAPI con MySQL (XAMPP)...
echo ========================================================
echo.
echo Recuerda tener encendido el servicio MySQL en tu panel de XAMPP.
echo.

cd /d "%~dp0"

echo Abriendo navegador en http://localhost:8000...
start http://localhost:8000

echo Iniciando backend FastAPI...
python main.py

pause

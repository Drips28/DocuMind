@echo off
title DocuMind AI - Iniciando sistema...
cd /d %~dp0

if not exist venv (
    echo [1/3] Creando entorno virtual por primera vez...
    python -m venv venv
    echo [2/3] Instalando dependencias desde requirements.txt...
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo [1/2] Activando entorno virtual...
    call venv\Scripts\activate
)

echo [2/2] Lanzando aplicacion web en el navegador...
streamlit run app.py
pause
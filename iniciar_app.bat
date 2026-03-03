@echo off
echo Iniciando Gestor de Actividades...
echo Por favor espere...
start http://localhost:8000
pushd "%~dp0"
python Actividades\app_web.py
popd
pause

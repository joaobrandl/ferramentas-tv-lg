@echo off
rem Tira o Free My TV da lista de entradas da TV (desfaz o "ligar a TV ja no Free My TV").
rem A TV precisa estar ligada e no cabo do PC. O IP dela e procurado pelo cabo (muda quando falta luz).
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "IP="
for /f "delims=" %%i in ('""%PY%" -I "%~dp0achar_tv.py""') do set "IP=%%i"
if not defined IP (
  echo Nao achei a TV no cabo do PC. Confira se ela esta ligada e com o cabo no PC.
  pause
  exit /b 1
)
echo TV encontrada em %IP%
"%PY%" "%~dp0tvctl.py" %IP% luna "luna://com.webos.service.eim/deleteDevice" "{\"appId\":\"io.freemytv\"}"
pause

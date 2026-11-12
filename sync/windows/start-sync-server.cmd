@echo off
REM Keep this running on the Windows machine. Nothing to install: Python 3 from python.org is enough,
REM and this file makes no other assumptions.
REM
REM First run: set TOKEN to any long random string, and copy the same string into the phone's sync.json.

setlocal
set ROOT=%USERPROFILE%\QuixiDesk
set TOKEN=CHANGE-ME-TO-A-LONG-RANDOM-STRING
set PORT=8788

if not exist "%ROOT%" mkdir "%ROOT%"
echo Serving %ROOT% on port %PORT%
python "%~dp0..\sync_server.py" --root "%ROOT%" --token "%TOKEN%" --port %PORT%
pause

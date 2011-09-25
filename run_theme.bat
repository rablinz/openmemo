@echo off
:repeat
    python openmemo/themes/server/core/server_app.py "%1" "%2"
if %errorlevel% == 3 goto repeat
if %errorlevel% == 1 goto error
goto end
:error
pause
:end

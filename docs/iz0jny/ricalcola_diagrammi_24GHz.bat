@echo off
rem FeedLab - ricalcola S11 e diagrammi dai dati in sim_data (dopo la simulazione completa), pochi secondi
cd /d "%~dp0"
if not defined OPENEMS_INSTALL_PATH set "OPENEMS_INSTALL_PATH=C:\Program Files\openEMS_x64_v0.37.0_msvc\openEMS"
set "PY=%LOCALAPPDATA%\Programs\FeedLab\python\python.exe"
if not exist "%PY%" set "PY=python"
echo openEMS: %OPENEMS_INSTALL_PATH%
echo Python: %PY%
"%PY%" -u sim_iz0jny_24048_fD065.py --post
echo.
echo Finito: il file results.json si trova in questa cartella.
pause

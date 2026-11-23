@echo off
rem FeedLab - simulazione openEMS del feed IZ0JNY Dual-Flare 24.048 GHz (f/D 0.65)
cd /d "%~dp0"
if not defined OPENEMS_INSTALL_PATH set "OPENEMS_INSTALL_PATH=C:\Program Files\openEMS_x64_v0.37.0_msvc\openEMS"
set "PY=%LOCALAPPDATA%\Programs\FeedLab\python\python.exe"
if not exist "%PY%" set "PY=python"
echo openEMS: %OPENEMS_INSTALL_PATH%
echo Python: %PY%
"%PY%" -u sim_iz0jny_24048_fD065.py %*
echo.
echo Finito: il file results.json e in questa cartella.
pause

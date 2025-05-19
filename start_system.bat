@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo          Smart AC Control System Launcher
echo ========================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ERROR: Python not found!
    echo Please make sure Python is installed and in your PATH.
    pause
    exit /b 1
)

REM Make sure we're in the correct directory
echo Working directory: %CD%
echo.

REM Check for required files
set MISSING_FILES=0
if not exist "mqtt_config.py" set /A MISSING_FILES+=1
if not exist "data_manager\db.py" set /A MISSING_FILES+=1
if not exist "data_manager\manager.py" set /A MISSING_FILES+=1
if not exist "emulators\dht_emulator.py" set /A MISSING_FILES+=1
if not exist "emulators\knob_emulator.py" set /A MISSING_FILES+=1
if not exist "emulators\relay_emulator.py" set /A MISSING_FILES+=1
if not exist "gui\main_gui.py" set /A MISSING_FILES+=1

if !MISSING_FILES! NEQ 0 (
    color 0C
    echo.
    echo One or more required files are missing.
    echo Please make sure all files are in the correct directories.
    pause
    exit /b 1
)

REM Install dependencies if needed
if exist "requirements.txt" (
    echo Installing required packages...
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: Some packages might not have installed correctly.
        echo The system will try to run anyway.
        echo.
    )
)

:menu
cls
color 0A
echo.
echo ========================================================
echo           Smart AC Control System - Menu
echo ========================================================
echo.
echo Choose an option:
echo.
echo [1] Start All Components (Recommended)
echo [2] Start Only Data Manager
echo [3] Start Only DHT Emulator
echo [4] Start Only Knob Emulator
echo [5] Start Only Relay Emulator
echo [6] Start Main GUI Launcher
echo [7] Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_manager
if "%choice%"=="3" goto start_dht
if "%choice%"=="4" goto start_knob
if "%choice%"=="5" goto start_relay
if "%choice%"=="6" goto start_gui
if "%choice%"=="7" goto end

echo Invalid choice! Please try again.
timeout /t 2 /nobreak > nul
goto menu

:start_all
echo.
echo Starting Main GUI Launcher (will start all components)...
start "Smart AC Main GUI" cmd /k "color 0B && python gui\main_gui.py || (color 0C && echo ERROR: Main GUI failed to start! && pause)"
goto end

:start_manager
echo.
echo Starting Data Manager...
start "Data Manager" cmd /k "color 0B && python data_manager\manager.py || (color 0C && echo ERROR: Data Manager failed to start! && pause)"
goto end

:start_dht
echo.
echo Starting DHT Temperature Sensor...
start "DHT Emulator" cmd /k "color 0A && python emulators\dht_emulator.py || (color 0C && echo ERROR: DHT Emulator failed to start! && pause)"
goto end

:start_knob
echo.
echo Starting Temperature Setpoint Knob...
start "Knob Emulator" cmd /k "color 0E && python emulators\knob_emulator.py || (color 0C && echo ERROR: Knob Emulator failed to start! && pause)"
goto end

:start_relay
echo.
echo Starting AC Relay Control...
start "Relay Emulator" cmd /k "color 09 && python emulators\relay_emulator.py || (color 0C && echo ERROR: Relay Emulator failed to start! && pause)"
goto end

:start_gui
echo.
echo Starting Main GUI...
start "Main GUI" cmd /k "color 0D && python gui\main_gui.py || (color 0C && echo ERROR: Main GUI failed to start! && pause)"
goto end

:end
echo.
echo ========================================================
echo              Operation Complete!
echo ========================================================
echo.
echo To close the system, simply close all component windows.
echo. 
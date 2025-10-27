@echo off
REM DuckParqStream Startup Script for Windows

echo ============================================================
echo DuckParqStream - Local JSON Database
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import duckdb" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [OK] All dependencies installed
echo.

REM Ask user what to do
echo What would you like to do?
echo.
echo 1. Start Web Interface
echo 2. Run Examples
echo 3. Generate Test Data
echo 4. View Statistics
echo 5. Exit
echo.

choice /C 12345 /N /M "Enter your choice (1-5): "

if errorlevel 5 goto :end
if errorlevel 4 goto :stats
if errorlevel 3 goto :generate
if errorlevel 2 goto :examples
if errorlevel 1 goto :start

:start
echo.
echo [STARTING] Launching web interface...
echo.
python run.py
goto :end

:examples
echo.
echo [RUNNING] Executing examples...
echo.
python example.py
echo.
pause
goto :end

:generate
echo.
set /p COUNT="How many records to generate? (default: 1000): "
if "%COUNT%"=="" set COUNT=1000
echo.
echo [GENERATING] Creating %COUNT% test records...
python run.py generate --type user --count %COUNT%
echo.
pause
goto :end

:stats
echo.
echo [STATISTICS] Dataset information:
echo.
python run.py stats
echo.
pause
goto :end

:end
echo.
echo Goodbye!

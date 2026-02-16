@echo off
REM Competitive Intelligence Agent - Windows Task Scheduler Runner
REM This script runs the agent on Windows

REM Configuration
SET PROJECT_DIR=C:\path\to\your\competitive-intel-agent
SET LOG_DIR=%PROJECT_DIR%\logs
SET LOG_FILE=%LOG_DIR%\agent_%DATE:~-4%%DATE:~4,2%%DATE:~7,2%.log

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Change to project directory
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo Error: Could not change to project directory >> "%LOG_FILE%"
    exit /b 1
)

REM Log start
echo ========================================== >> "%LOG_FILE%"
echo [%DATE% %TIME%] Starting Competitive Intelligence Agent >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo [%DATE% %TIME%] Activating virtual environment... >> "%LOG_FILE%"
    call venv\Scripts\activate.bat
)

REM Run the agent
echo [%DATE% %TIME%] Running agent... >> "%LOG_FILE%"
python competitive_intelligence_agent.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] Error: Agent failed >> "%LOG_FILE%"
    exit /b 1
)
echo [%DATE% %TIME%] Agent executed successfully >> "%LOG_FILE%"

REM Generate report
echo [%DATE% %TIME%] Generating HTML report... >> "%LOG_FILE%"
python generate_report.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] Error: Report generation failed >> "%LOG_FILE%"
    exit /b 1
)
echo [%DATE% %TIME%] Report generated successfully >> "%LOG_FILE%"

REM Clean up old logs (older than 30 days)
forfiles /p "%LOG_DIR%" /m agent_*.log /d -30 /c "cmd /c del @path" 2>nul

echo [%DATE% %TIME%] Agent run completed >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

REM Exit successfully
exit /b 0
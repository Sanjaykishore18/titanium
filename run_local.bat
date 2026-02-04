@echo off
REM ============================================================================
REM Titanium Backend & Frontend Local Runner (Windows) - IMPROVED
REM Save as: run_local.bat in D:\PROJECTS\titanium\
REM ============================================================================

title Titanium Local Dev Server

echo ========================================
echo   Titanium Local Development Setup
echo ========================================
echo.

REM ============================================
REM Get local IP address
REM ============================================
set LOCAL_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
    goto :found
)
:found
set LOCAL_IP=%LOCAL_IP: =%

if "%LOCAL_IP%"=="" (
    set LOCAL_IP=127.0.0.1
    echo WARNING: Could not detect IP address. Using 127.0.0.1
) else (
    echo Detected local IP: %LOCAL_IP%
)

REM ============================================
REM Pre-flight checks
REM ============================================
echo.
echo [1/4] Checking prerequisites...
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   ✓ Python found

REM Check Redis
where redis-server >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Redis is not installed or not in PATH
    echo Please install Redis from: https://github.com/microsoftarchive/redis/releases
    echo.
    set /p CONTINUE="Continue without Redis? (y/n): "
    if /i not "%CONTINUE%"=="y" exit /b 1
) else (
    echo   ✓ Redis found
)

REM Check if backend directory exists
if not exist "backend\" (
    echo ERROR: backend\ directory not found
    echo Please run this script from D:\PROJECTS\titanium\
    pause
    exit /b 1
)
echo   ✓ Backend directory found

REM Check if frontend directory exists
if not exist "frontend\" (
    echo ERROR: frontend\ directory not found
    echo Please run this script from D:\PROJECTS\titanium\
    pause
    exit /b 1
)
echo   ✓ Frontend directory found

REM ============================================
REM Install/Check Python dependencies
REM ============================================
echo.
echo [2/4] Checking Python dependencies...
echo.

cd backend
python -c "import django" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing backend dependencies...
    pip install -r requirements.txt --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install dependencies
        cd ..
        pause
        exit /b 1
    )
)
echo   ✓ Backend dependencies ready
cd ..

REM ============================================
REM Start services
REM ============================================
echo.
echo [3/4] Starting services...
echo.

REM Start Redis (if available)
where redis-server >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Starting Redis on port 6379...
    start /B "Redis" redis-server --save "" --appendonly no
    timeout /t 2 /nobreak >nul
    echo   ✓ Redis started
)

REM Start Backend with Daphne
echo Starting Backend (Daphne) on port 8000...
cd backend
start /B "Backend" cmd /c "python -m daphne -b 0.0.0.0 -p 8000 escape_game_project.asgi:application 2>&1"
cd ..
timeout /t 3 /nobreak >nul
echo   ✓ Backend started

REM Start Frontend with Python HTTP Server
echo Starting Frontend (HTTP Server) on port 8080...
cd frontend
start /B "Frontend" cmd /c "python -m http.server 8080 --bind %LOCAL_IP% 2>&1"
cd ..
timeout /t 2 /nobreak >nul
echo   ✓ Frontend started

REM ============================================
REM Display access information
REM ============================================
echo.
echo [4/4] All services running!
echo.
echo ========================================
echo   ACCESS YOUR APPLICATION
echo ========================================
echo.
echo   Local:     http://localhost:8080
echo   Network:   http://%LOCAL_IP%:8080
echo.
echo   Backend:   http://localhost:8000
echo   Redis:     %LOCAL_IP%:6379
echo.
echo ========================================
echo   SERVICE STATUS
echo ========================================
echo.

REM Show running processes
tasklist /FI "WINDOWTITLE eq Redis*" 2>nul | find "cmd.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Redis running
) else (
    echo   ✗ Redis not running
)

tasklist /FI "WINDOWTITLE eq Backend*" 2>nul | find "cmd.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Backend running
) else (
    echo   ✗ Backend not running
)

tasklist /FI "WINDOWTITLE eq Frontend*" 2>nul | find "cmd.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Frontend running
) else (
    echo   ✗ Frontend not running
)

echo.
echo ========================================
echo   CONTROLS
echo ========================================
echo.
echo   Press 's' to see service status
echo   Press 'o' to open browser
echo   Press 'q' to stop all services
echo.

REM ============================================
REM Interactive loop
REM ============================================
:menu
set /p choice="Enter command (s/o/q): "

if /i "%choice%"=="s" (
    echo.
    echo Service Status:
    netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ Backend on port 8000
    ) else (
        echo   ✗ Backend not on port 8000
    )
    
    netstat -ano | findstr ":8080 " | findstr "LISTENING" >nul
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ Frontend on port 8080
    ) else (
        echo   ✗ Frontend not on port 8080
    )
    
    netstat -ano | findstr ":6379 " | findstr "LISTENING" >nul
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ Redis on port 6379
    ) else (
        echo   ✗ Redis not on port 6379
    )
    echo.
    goto menu
)

if /i "%choice%"=="o" (
    echo Opening browser...
    start http://localhost:8080
    goto menu
)

if /i "%choice%"=="q" goto cleanup

goto menu

REM ============================================
REM Cleanup
REM ============================================
:cleanup
echo.
echo Stopping all services...

REM Kill specific windows by title (safer than killing all python)
taskkill /FI "WINDOWTITLE eq Redis*" /F /T >nul 2>nul
taskkill /FI "WINDOWTITLE eq Backend*" /F /T >nul 2>nul
taskkill /FI "WINDOWTITLE eq Frontend*" /F /T >nul 2>nul

REM Alternative: Kill by port if above doesn't work
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do (
    taskkill /PID %%a /F >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 "') do (
    taskkill /PID %%a /F >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":6379 "') do (
    taskkill /PID %%a /F >nul 2>nul
)

timeout /t 1 /nobreak >nul

echo.
echo ========================================
echo   All services stopped
echo ========================================
echo.
pause
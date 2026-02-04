@echo off
REM ============================================================================
REM DOCKER RESTART SCRIPT (Windows)
REM Save as: restart_docker.bat in D:\PROJECTS\titanium\
REM ============================================================================

echo.
echo ========================================
echo   RESTARTING DOCKER CONTAINERS
echo ========================================
echo.

echo [1/4] Stopping all containers...
docker-compose down
if %errorlevel% neq 0 (
    echo ERROR: Failed to stop containers
    pause
    exit /b 1
)

echo.
echo [2/4] Cleaning up old containers...
docker container prune -f

echo.
echo [3/4] Rebuilding images...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo ERROR: Failed to build images
    pause
    exit /b 1
)

echo.
echo [4/4] Starting containers...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start containers
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! Containers are running
echo ========================================
echo.
echo Access your app at:
echo   Local:   http://localhost:8080
echo.
echo View logs with:
echo   docker-compose logs -f
echo.
echo Press any key to view container status...
pause > nul

docker-compose ps

echo.
echo Press any key to exit...
pause > nul
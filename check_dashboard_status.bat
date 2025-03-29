@echo off
setlocal enabledelayedexpansion

echo Checking FMS Dashboard Status...
echo.

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. The dashboard cannot be accessed.
    goto :end
)

:: Check if the container is running
docker ps | findstr fms-dashboard >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FMS Dashboard container is not running.
    
    :: Check if the container exists but is stopped
    docker ps -a | findstr fms-dashboard >nul 2>&1
    if %errorlevel% equ 0 (
        echo The container exists but is stopped. You can start it with:
        echo docker start fms-dashboard
        echo.
        echo Or run auto_start_dashboard.bat to restart it automatically.
    ) else (
        echo The container does not exist. Run auto_start_dashboard.bat to create and start it.
    )
    goto :end
)

:: Get container information
for /f "tokens=1,2,3,4,5,6,7,8" %%a in ('docker ps ^| findstr fms-dashboard') do (
    set CONTAINER_ID=%%a
    set IMAGE=%%b
    set STATUS=%%e %%f %%g
    set PORTS=%%h
)

echo [SUCCESS] FMS Dashboard is running!
echo.
echo Container ID: !CONTAINER_ID!
echo Image: !IMAGE!
echo Status: !STATUS!
echo Ports: !PORTS!
echo.
echo The dashboard is accessible at: http://localhost:8501
echo.
echo To view container logs, run: docker logs fms-dashboard
echo To restart the container, run: docker restart fms-dashboard
echo To stop the container, run: docker stop fms-dashboard

:end
pause

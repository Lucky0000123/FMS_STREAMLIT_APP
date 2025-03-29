@echo off
echo Starting FMS Dashboard on port 8501...

:: Set the current directory to the script location
cd /d "%~dp0"

:: Create logs directory if it doesn't exist
if not exist "%~dp0logs" mkdir "%~dp0logs"

:: Log file path
set LOG_FILE="%~dp0logs\docker_startup_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set LOG_FILE=%LOG_FILE: =0%

echo Starting FMS Dashboard Docker container at %date% %time% > %LOG_FILE%

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Starting Docker... >> %LOG_FILE%
    echo Docker is not running. Starting Docker...
    
    :: Try to start Docker Desktop
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo Docker Desktop not found at the expected location. >> %LOG_FILE%
        echo Docker Desktop not found at the expected location.
        echo Please start Docker manually or install it if not installed.
        goto :error
    )
    
    :: Wait for Docker to start
    echo Waiting for Docker to start... >> %LOG_FILE%
    echo Waiting for Docker to start...
    
    :: Try for 2 minutes (12 attempts, 10 seconds each)
    for /l %%i in (1, 1, 12) do (
        timeout /t 10 /nobreak > nul
        docker info >nul 2>&1
        if !errorlevel! equ 0 (
            echo Docker started successfully. >> %LOG_FILE%
            echo Docker started successfully.
            goto :docker_running
        )
        echo Waiting for Docker to start (attempt %%i of 12)... >> %LOG_FILE%
        echo Waiting for Docker to start (attempt %%i of 12)...
    )
    
    echo Docker failed to start after waiting. >> %LOG_FILE%
    echo Docker failed to start after waiting.
    goto :error
)

:docker_running
echo Docker is running. >> %LOG_FILE%
echo Docker is running.

:: Check if the container is already running
docker ps | findstr fms-dashboard >nul 2>&1
if %errorlevel% equ 0 (
    echo FMS Dashboard is already running. >> %LOG_FILE%
    echo FMS Dashboard is already running.
) else (
    :: Check if the container exists but is stopped
    docker ps -a | findstr fms-dashboard >nul 2>&1
    if %errorlevel% equ 0 (
        echo Starting existing FMS Dashboard container... >> %LOG_FILE%
        echo Starting existing FMS Dashboard container...
        docker start fms-dashboard >> %LOG_FILE% 2>&1
        if %errorlevel% neq 0 (
            echo Failed to start existing container. Rebuilding... >> %LOG_FILE%
            echo Failed to start existing container. Rebuilding...
            goto :rebuild_container
        )
    ) else (
        :rebuild_container
        echo Building and starting FMS Dashboard container... >> %LOG_FILE%
        echo Building and starting FMS Dashboard container...
        docker-compose up -d --build >> %LOG_FILE% 2>&1
        if %errorlevel% neq 0 (
            echo Failed to build and start container. >> %LOG_FILE%
            echo Failed to build and start container.
            goto :error
        )
    )
)

:: Verify the container is running
timeout /t 5 /nobreak > nul
docker ps | findstr fms-dashboard >nul 2>&1
if %errorlevel% neq 0 (
    echo Container failed to start properly. >> %LOG_FILE%
    echo Container failed to start properly.
    goto :error
)

echo FMS Dashboard is now running on http://localhost:8501 >> %LOG_FILE%
echo FMS Dashboard is now running on http://localhost:8501
echo Dashboard started successfully at %date% %time% >> %LOG_FILE%
goto :end

:error
echo Error occurred during startup at %date% %time% >> %LOG_FILE%
echo Error occurred during startup. Check the log file: %LOG_FILE%
exit /b 1

:end
exit /b 0

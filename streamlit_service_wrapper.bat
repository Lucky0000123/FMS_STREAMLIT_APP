@echo off
setlocal

:: Set environment variables for SQL connection
set STREAMLIT_SERVER_PORT=8501
set STREAMLIT_SERVER_ADDRESS=0.0.0.0
set SQL_SERVER=10.211.10.2
set SQL_DATABASE=FMS_DB
set SQL_USERNAME=headofnickel
set SQL_PASSWORD=Dataisbeautifulrev001!

:: Get the current directory (where this script is located)
set CURRENT_DIR=%~dp0
cd /d "%CURRENT_DIR%"

:: Path to Python in virtual environment
set PYTHON_EXE="%CURRENT_DIR%venv\Scripts\python.exe"

:: Run Streamlit (use call to ensure it waits for completion)
call %PYTHON_EXE% -m streamlit run "%CURRENT_DIR%Homepage.py" --server.port=8501 --server.address=0.0.0.0 --server.maxUploadSize=200

:: If Streamlit exits, wait a bit and restart
timeout /t 10
goto :eof

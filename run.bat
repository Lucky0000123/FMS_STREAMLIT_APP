@echo off
REM ==========================================================
REM Deploying the Streamlit Application
REM ==========================================================

REM Step 1: Activate the virtual environment
echo Activating the virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Virtual environment activation failed.
    pause
    exit /b 1
)

REM Step 2: Install required packages
echo Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package installation encountered an issue.
    pause
    exit /b 1
)

REM Step 3: Start the Streamlit application in headless mode on port 8501
echo Starting the Streamlit application on port 8501...
streamlit run homepage.py --server.headless true --server.port 8501 > streamlit.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to launch the Streamlit application.
    pause
    exit /b 1
)

echo Application started successfully. Refer to streamlit.log for details.
pause

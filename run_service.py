import os
import sys
import subprocess
import time
from pathlib import Path

def run_streamlit():
    # Get the absolute path to the virtual environment
    venv_path = Path(__file__).parent / "venv"
    python_path = venv_path / "Scripts" / "python.exe"
    
    # Get the absolute path to the Homepage.py
    homepage_path = Path(__file__).parent / "Homepage.py"
    
    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    
    # Run the Streamlit app
    try:
        subprocess.run([
            str(python_path),
            "-m",
            "streamlit",
            "run",
            str(homepage_path),
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.maxUploadSize=200",
            "--browser.serverAddress=0.0.0.0",
            "--browser.serverPort=8501",
            "--browser.gatherUsageStats=false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_streamlit()
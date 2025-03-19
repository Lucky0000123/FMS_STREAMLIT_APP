import os
import subprocess

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the Streamlit app
app_path = os.path.join(current_dir, "1_🏭_Homepage.py")

# Run the Streamlit app
subprocess.run(["streamlit", "run", app_path]) 

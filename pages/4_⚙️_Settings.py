# Import necessary libraries
import streamlit as st
import os
import sys
import platform
import pandas as pd
import pyodbc
import logging
from datetime import datetime
import time

# Set page config
st.set_page_config(
    page_title="Settings & Diagnostics",
    page_icon="⚙️",
    layout="wide"
)

# Import local modules
from utils import render_glow_line, render_header, get_sql_connection
from translations import get_translation
from config import DB_CONFIG, GLOBAL_CSS

# Apply global CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Page Header
render_header("Settings & Diagnostics", "", icon_path="assets/settings.png")
render_glow_line()

# Function to test database connection
def test_db_connection(host, database, username=None, password=None, trusted_connection=False, driver=None):
    """Test database connection and return the result"""
    try:
        # Create connection string
        conn_str = f'DRIVER={{{driver or "ODBC Driver 17 for SQL Server"}}};SERVER={host};DATABASE={database};'
        
        if trusted_connection:
            conn_str += 'Trusted_Connection=yes;'
        else:
            conn_str += f'UID={username};PWD={password}'
        
        # Try to connect
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT @@version")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return True, version
    
    except Exception as e:
        return False, str(e)

# Create three tabs
tab_db, tab_system, tab_logs = st.tabs(["Database Connection", "System Info", "Logs"])

with tab_db:
    st.markdown("## SQL Server Configuration")
    st.markdown("Configure and test your connection to the SQL Server database.")
    
    # Check if there's a stored error
    if 'sql_connection_error' in st.session_state:
        st.error(f"Last SQL Error: {st.session_state.sql_connection_error}")
    
    # Show SQL data date range if available
    if 'sql_date_range' in st.session_state:
        st.info(f"📅 Current SQL data range: {st.session_state.sql_date_range}")
    
    # Show current data source
    if 'data_source' in st.session_state:
        data_source = st.session_state.data_source
        if data_source == "sql":
            st.success("✅ Currently using SQL database")
        elif data_source == "upload":
            st.info("ℹ️ Currently using uploaded file")
        elif data_source == "network":
            st.info("ℹ️ Currently using network dataset")
        elif data_source == "sample":
            st.warning("⚠️ Currently using sample dataset")
    
    # Add clear cache button
    if st.button("🔄 Clear Data Cache"):
        # This will clear Streamlit's cache
        st.cache_data.clear()
        # Also clear session state data
        if 'df' in st.session_state:
            del st.session_state.df
        st.success("✅ Cache cleared! Data will be reloaded from source.")
        time.sleep(1)
        st.rerun()
    
    # Create form for database settings
    with st.form("db_settings"):
        # Check if we have secrets
        has_secrets = hasattr(st, 'secrets') and 'sql' in st.secrets
        
        # Fill in defaults from secrets or config
        if has_secrets:
            default_host = st.secrets.sql.host
            default_db = st.secrets.sql.database
            default_user = st.secrets.sql.username if hasattr(st.secrets.sql, 'username') else ""
            default_pass = st.secrets.sql.password if hasattr(st.secrets.sql, 'password') else ""
            default_driver = st.secrets.sql.driver
            default_trusted = hasattr(st.secrets.sql, 'trusted_connection') and st.secrets.sql.trusted_connection.lower() == 'yes'
        else:
            default_host = DB_CONFIG.get('server', '')
            default_db = DB_CONFIG.get('database', '')
            default_user = ""
            default_pass = ""
            default_driver = DB_CONFIG.get('driver', '{SQL Server}').strip('{}')
            default_trusted = DB_CONFIG.get('trusted_connection', 'no') == 'yes'
        
        # Create form inputs
        col1, col2 = st.columns(2)
        
        with col1:
            host = st.text_input("SQL Server Host/IP", value=default_host)
            database = st.text_input("Database Name", value=default_db)
            auth_type = st.radio("Authentication Type", ["SQL Authentication", "Windows Authentication"], 
                               index=1 if default_trusted else 0)
            
        with col2:
            driver = st.text_input("ODBC Driver", value=default_driver)
            if auth_type == "SQL Authentication":
                username = st.text_input("Username", value=default_user)
                password = st.text_input("Password", value=default_pass, type="password")
                trusted_connection = False
            else:
                username = ""
                password = ""
                trusted_connection = True
                st.info("Windows Authentication uses the current Windows user credentials")
        
        # Submit button
        submitted = st.form_submit_button("Test Connection")
        
        # If submitted, test connection
        if submitted:
            with st.spinner("Testing connection..."):
                success, message = test_db_connection(
                    host=host,
                    database=database,
                    username=username,
                    password=password,
                    trusted_connection=trusted_connection,
                    driver=driver
                )
            
            if success:
                st.success(f"✅ Connection successful!\n\nSQL Server Version: {message}")
                
                # Show how to update secrets.toml
                with st.expander("How to update your secrets.toml file"):
                    st.markdown("Copy the following configuration to your `.streamlit/secrets.toml` file:")
                    
                    if trusted_connection:
                        config_code = f"""
                        [sql]
                        host = "{host}"
                        database = "{database}"
                        driver = "{driver}"
                        trusted_connection = "yes"
                        """
                    else:
                        config_code = f"""
                        [sql]
                        host = "{host}"
                        database = "{database}"
                        username = "{username}"
                        password = "{password}"
                        driver = "{driver}"
                        """
                    
                    st.code(config_code.strip(), language="toml")
            else:
                st.error(f"❌ Connection failed: {message}")
                
                # Show common troubleshooting tips
                with st.expander("Troubleshooting Tips"):
                    st.markdown("""
                    ### Common SQL Server Connection Issues:
                    
                    1. **Server not reachable**: Check if the SQL Server is running and reachable from this machine
                    2. **Firewall blocking**: Make sure the SQL Server port (usually 1433) is not blocked by firewall
                    3. **Authentication issues**: Verify username and password or Windows Authentication settings
                    4. **Database doesn't exist**: Confirm the database name is correct
                    5. **Driver not installed**: Make sure the ODBC driver is installed on this machine
                    
                    ### For Windows Authentication:
                    - The application must be running under a Windows user that has access to the SQL Server
                    
                    ### For SQL Authentication:
                    - SQL Server must be configured to allow SQL Authentication
                    - The user must have proper permissions to the database
                    """)

with tab_system:
    st.markdown("## System Information")
    
    # Get system info
    os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
    python_ver = sys.version
    
    # ODBC Drivers
    try:
        drivers = pyodbc.drivers()
        odbc_drivers = ", ".join(drivers) if drivers else "No ODBC drivers found"
    except:
        odbc_drivers = "Unable to retrieve ODBC drivers"
    
    # Display system info
    st.markdown("### Environment Details")
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"**OS:** {os_info}")
        st.markdown(f"**Python Version:** {python_ver}")
        st.markdown(f"**Streamlit Version:** {st.__version__}")
    
    with info_col2:
        st.markdown(f"**PyODBC Version:** {pyodbc.version}")
        st.markdown(f"**Pandas Version:** {pd.__version__}")
        st.markdown(f"**Available ODBC Drivers:**")
        
        if isinstance(odbc_drivers, str):
            st.markdown(f"- {odbc_drivers}")
        else:
            for driver in odbc_drivers:
                st.markdown(f"- {driver}")

with tab_logs:
    st.markdown("## Application Logs")
    
    # Create a button to refresh logs
    if st.button("Refresh Logs"):
        st.rerun()
    
    # Check if there are logs
    log_file = "app.log"
    if os.path.exists(log_file):
        # Read the last 100 lines
        with open(log_file, "r") as f:
            logs = f.readlines()[-100:]
        
        # Format logs
        st.markdown("### Recent Logs (last 100 lines)")
        st.code("".join(logs), language="log") 
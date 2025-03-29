"""
Utility functions for the FMS Safety Dashboard.

This module provides functions for data processing, SQL connectivity,
UI rendering (headers, chart titles, dividers, file uploads), theme switching,
and data filtering.
"""

import os
import time
import json
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, Any, Dict

import pyodbc
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

# Local module imports
from config import (
    THEME_CONFIG,
    GLOBAL_CSS,
    RISK_THRESHOLDS,
    UPLOAD_CONFIG,
    PDF_CONFIG,
    DB_CONFIG,
)
from translations import TRANSLATIONS, get_translation


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a dataframe to ensure it has the correct column formats and values.
    
    Args:
        df: The dataframe to process
        
    Returns:
        The processed dataframe
    """
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Process date columns
    if "Shift Date" in df.columns:
        df["Shift Date"] = pd.to_datetime(df["Shift Date"], errors="coerce")
        df.dropna(subset=["Shift Date"], inplace=True)
        df["Date"] = df["Shift Date"].dt.date
    
    # Process shift values (capitalize)
    if "Shift" in df.columns:
        df["Shift"] = df["Shift"].astype(str).str.capitalize()
    
    # Ensure driver names are clean
    if "Driver" in df.columns:
        df["Driver"] = df["Driver"].fillna("").astype(str).str.strip()
    
    return df


def assign_risk_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign risk levels to each record based on the 'Overspeeding Value'.

    Risk level criteria:
      - 'Extreme' if the overspeeding value is greater than or equal to RISK_THRESHOLDS["Extreme"].
      - 'High' if the overspeeding value is between RISK_THRESHOLDS["High"] (inclusive)
        and RISK_THRESHOLDS["Extreme"].
      - 'Medium' otherwise.
    
    Parameters:
        df (pd.DataFrame): The DataFrame containing the 'Overspeeding Value' column.
        
    Returns:
        pd.DataFrame: The DataFrame with a new 'Risk Level' column.
    """
    if "Overspeeding Value" in df.columns:
        df["Overspeeding Value"] = pd.to_numeric(df["Overspeeding Value"], errors="coerce")
        conditions = [
            df["Overspeeding Value"] >= RISK_THRESHOLDS["Extreme"],
            (df["Overspeeding Value"] >= RISK_THRESHOLDS["High"]) & (df["Overspeeding Value"] < RISK_THRESHOLDS["Extreme"]),
            df["Overspeeding Value"] < RISK_THRESHOLDS["High"]
        ]
        choices = ["Extreme", "High", "Medium"]
        df["Risk Level"] = np.select(conditions, choices, default="Medium")
    else:
        df["Risk Level"] = "Medium"
    return df


def get_sql_connection() -> Optional[pyodbc.Connection]:
    """
    Establish and return a connection to the SQL Server database using the provided configuration.

    Returns:
        pyodbc.Connection or None: The SQL connection object if the connection is successful;
        otherwise, None.
    """
    try:
        # Try to use secrets.toml first
        if hasattr(st, 'secrets') and 'sql' in st.secrets:
            # Log attempt before connecting
            logging.info(f"Attempting SQL connection to {st.secrets.sql.host}/{st.secrets.sql.database}")
            
            # Build connection string
            conn_str = (
                f'DRIVER={{{st.secrets.sql.driver}}};'
                f'SERVER={st.secrets.sql.host};'
                f'DATABASE={st.secrets.sql.database};'
            )
            
            # Check if using Windows Authentication or SQL Authentication
            if hasattr(st.secrets.sql, 'trusted_connection') and st.secrets.sql.trusted_connection.lower() == 'yes':
                conn_str += 'Trusted_Connection=yes;'
                logging.info("Using Windows Authentication for SQL connection")
            else:
                conn_str += f'UID={st.secrets.sql.username};PWD={st.secrets.sql.password}'
                logging.info(f"Using SQL Authentication with username: {st.secrets.sql.username}")
            
            # Try connecting with the built connection string
            try:
                conn = pyodbc.connect(conn_str)
                logging.info(f"Successfully connected to SQL Server")
                
                # Clear any previous errors
                if 'sql_connection_error' in st.session_state:
                    del st.session_state.sql_connection_error
                
                return conn
            except Exception as inner_e:
                error_msg = f"SQL connection failed: {str(inner_e)}"
                logging.error(error_msg)
                st.session_state.sql_connection_error = error_msg
                # Don't show error to user
                return None
        # Fallback to hardcoded credentials for local development
        else:
            # Don't attempt connection if we don't have secrets
            msg = "No SQL credentials found in secrets.toml"
            logging.warning(msg)
            st.session_state.sql_connection_error = msg
            # Don't show error to user
            return None
    except Exception as e:
        # Log the error but don't show it to the user
        error_msg = f"Unexpected error setting up SQL connection: {e}"
        logging.error(error_msg)
        # Store the error in session state for diagnostics
        st.session_state.sql_connection_error = error_msg
        return None


def render_header(title: str, subtitle: str = "", icon_path: Optional[str] = None, icon_width: int = 80) -> None:
    """
    Render a styled header with gradient background, title, subtitle, and an optional icon.

    Parameters:
        title (str): Header title text.
        subtitle (str, optional): Header subtitle text.
        icon_path (str, optional): File path to an icon image.
        icon_width (int, optional): Width of the icon image (default is 80).
    """
    # Apply global CSS styles
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # Build icon HTML if provided
    icon_html = f"""
    <div class="header-icon">
        <img src="{icon_path}" width="{icon_width}" />
    </div>
    """ if icon_path else ""

    subtitle_html = f'<div class="header-subtitle">{subtitle}</div>' if subtitle else ""

    header_html = f"""
    <div class="header-container" style="padding: 10px 15px; margin-bottom: 15px;">
      <div class="header-text">
        <h1 class="header-title" style="font-size: 26px; margin: 0; padding: 0;">{title}</h1>
        {subtitle_html}
      </div>
      {icon_html}
    </div>
    """

    st.markdown(header_html, unsafe_allow_html=True)


def fetch_sql_data() -> pd.DataFrame:
    """
    Retrieve data from the SQL Server database with a loading spinner.

    Returns:
        pd.DataFrame: DataFrame containing the fetched data, or an empty DataFrame on error.
    """
    with st.spinner(TRANSLATIONS[st.session_state.language].get("loading", "Loading")):
        conn = None
        try:
            conn = get_sql_connection()
            if conn:
                try:
                    query = "SELECT * FROM dbo.FMS_SPEED"
                    df = pd.read_sql(query, conn)
                    conn.close()
                    conn = None
                    return process_dataframe(df)  # Process the data before returning
                except Exception as e:
                    # Log the error but don't show it to the user
                    logging.error(f"SQL Query Error: {e}")
                    return pd.DataFrame()
                finally:
                    if conn:
                        try:
                            conn.close()
                        except:
                            pass
            else:
                return pd.DataFrame()
        except Exception as e:
            # Log the error but don't show it to the user
            logging.error(f"SQL fetch error: {e}")
            return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    """Load data from an uploaded file or a default dataset."""
    # Set up logging for data source
    if 'data_source' not in st.session_state:
        st.session_state.data_source = None
    
    # First check for uploaded file - prioritize this source
    uploaded_file = st.session_state.get("uploaded_file")
    if uploaded_file is not None:
        try:
            logging.info(f"Attempting to load data from uploaded file: {uploaded_file.name}")
            df = pd.read_excel(uploaded_file)
            st.session_state.using_default_data = False
            st.session_state.data_source = "upload"
            logging.info(f"Successfully loaded {len(df)} rows from uploaded file")
            st.success("✅ Uploaded dataset is now being used!")
            return process_dataframe(df)
        except Exception as e:
            error_msg = f"Failed to read uploaded file: {e}"
            logging.error(error_msg)
            st.error(f"⚠️ {error_msg}")
    
    # If no uploaded file, try SQL connection
    sql_error = None
    try:
        logging.info("Attempting to load data from SQL Server...")
        conn = get_sql_connection()
        if conn:
            try:
                # Execute query
                query = "SELECT * FROM dbo.FMS_SPEED"
                logging.info(f"Executing SQL query: {query}")
                
                # Start timer to measure query performance
                start_time = time.time()
                df = pd.read_sql(query, conn)
                query_time = time.time() - start_time
                
                conn.close()
                if not df.empty:
                    # Log date range information for debugging
                    if 'Shift Date' in df.columns:
                        min_date = pd.to_datetime(df['Shift Date']).min().date() if not df.empty else None
                        max_date = pd.to_datetime(df['Shift Date']).max().date() if not df.empty else None
                        logging.info(f"SQL data date range: {min_date} to {max_date}")
                        # Show date range in UI for debugging
                        st.session_state.sql_date_range = f"{min_date} to {max_date}"
                    
                    st.session_state.using_default_data = False
                    st.session_state.data_source = "sql"
                    logging.info(f"Successfully loaded {len(df)} rows from SQL Server in {query_time:.2f} seconds")
                    return process_dataframe(df)
            except Exception as e:
                # Log the error
                sql_error = f"SQL query failed: {str(e)}"
                logging.error(sql_error)
                st.session_state.sql_connection_error = sql_error
    except Exception as e:
        # Log the error
        sql_error = f"SQL connection failed: {str(e)}"
        logging.error(sql_error)
        st.session_state.sql_connection_error = sql_error
    
    # Try network file share (for local environment)
    DEFAULT_FILE_PATH = r"\\10.211.3.254\04. Mining\WBN - FLEET MANAGEMENT SYSTEM\Haulage DT Safety Event Report\FMS Event Data Query.xlsx"
    if os.path.exists(DEFAULT_FILE_PATH):
        try:
            logging.info(f"Attempting to load data from network file: {DEFAULT_FILE_PATH}")
            df = pd.read_excel(DEFAULT_FILE_PATH)
            st.session_state.using_default_data = True
            st.session_state.data_source = "network"
            logging.info(f"Successfully loaded {len(df)} rows from network file")
            st.info("ℹ️ Using network dataset.")
            return process_dataframe(df)
        except Exception as e:
            error_msg = f"Failed to read network file: {e}"
            logging.error(error_msg)
    
    # Final fallback - try local sample data in the repo (for cloud deployment)
    try:
        # Check if we have a sample data file in the data directory
        sample_file = "data/sample_fms_data.xlsx"
        if os.path.exists(sample_file):
            logging.info(f"Falling back to sample data: {sample_file}")
            df = pd.read_excel(sample_file)
            st.session_state.using_default_data = True
            st.session_state.data_source = "sample"
            logging.info(f"Successfully loaded {len(df)} rows from sample file")
            st.warning("⚠️ Using sample dataset. Connect to SQL or upload data for latest information.")
            return process_dataframe(df)
    except Exception as e:
        error_msg = f"Failed to read sample file: {e}"
        logging.error(error_msg)
    
    # If we get here, all attempts failed
    logging.critical("All data loading attempts failed!")
    st.error("⚠️ No data sources available. Please upload a file or check connection settings.")
    
    # Display connection diagnostics
    if sql_error:
        with st.expander("SQL Connection Diagnostics"):
            st.error(f"SQL Connection Error: {sql_error}")
            st.info("Please check the settings page to troubleshoot your SQL connection.")
            
            # Add button to go to settings page
            if st.button("Go to Settings & Diagnostics"):
                st.switch_page("pages/4_⚙️_Settings.py")
    
    return pd.DataFrame()


def load_lottie_json(json_path: str) -> Optional[Any]:
    """
    Load and return the content of a Lottie animation JSON file.

    Parameters:
        json_path (str): The file path to the Lottie JSON file.
    
    Returns:
        dict or None: Parsed JSON content if successful; otherwise, None.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(f"⚠️ Animation file not found: {json_path}")
    except json.JSONDecodeError as e:
        st.error(f"⚠️ Invalid JSON format in {json_path}: {e}")
    return None


def load_lottieurl(url: str) -> Optional[Any]:
    """
    Load a Lottie animation from a URL.

    Parameters:
        url (str): The URL to the Lottie animation JSON.
    
    Returns:
        dict or None: Parsed JSON content if successful; otherwise, None.
    """
    import requests
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"⚠️ Failed to load animation from URL: {url}, status code: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading animation from URL: {e}")
    return None


def render_chart_title(translation_key, lang=None):
    """Render an enhanced chart title with the appropriate translation."""
    try:
        # Use the provided language or fetch from session state
        if lang is None:
            lang = st.session_state.language
            
        # Get the translated text
        title_text = TRANSLATIONS[lang][translation_key]
        
        # Render the chart title with data attribute for specific styling
        st.markdown(f"""
        <div class="chart-title" data-chart="{translation_key}">
            <h2>{title_text}</h2>
        </div>
        """, unsafe_allow_html=True)
    except KeyError:
        # Fallback if translation is missing
        st.markdown(f"""
        <div class="chart-title">
            <h2>{translation_key}</h2>
        </div>
        """, unsafe_allow_html=True)


def render_glow_line() -> None:
    """
    Render a visually appealing separator line with a glow effect.
    """
    st.markdown(
        """
        <style>
            .glow-divider {
                height: 4px;
                background: linear-gradient(90deg, #ff8c42, #2a3f5f);
                box-shadow: 0 0 6px rgba(255, 140, 66, 0.6);
                margin: 20px 0;
                border-radius: 3px;
            }
        </style>
        <div class="glow-divider"></div>
        """,
        unsafe_allow_html=True
    )


def render_file_upload() -> None:
    """
    Render the file uploader widget for dataset uploads.
    """
    st.markdown("📁 **Upload Your Dataset (Excel)**")
    uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=UPLOAD_CONFIG["allowed_extensions"],
        help=f"Limit {UPLOAD_CONFIG['max_file_size']}MB per file • XLSX",
        key="file_upload_key"
    )
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.using_default_data = False
        st.success("✅ File uploaded successfully!")
    elif st.session_state.using_default_data:
        st.info("ℹ️ Using default dataset.")


def switch_theme():
    """Toggle between light and dark theme in the app."""
    # Check current theme setting
    current_theme = st.session_state.get("theme", "light")
    
    # Toggle theme
    new_theme = "dark" if current_theme == "light" else "light"
    st.session_state.theme = new_theme
    
    # Apply theme configuration
    if new_theme == "dark":
        # Dark theme colors
        st.session_state.text_color = "#FFFFFF"
        st.session_state.background_color = "#121212"
        st.session_state.accent_color = "#1D5B79"
    else:
        # Light theme colors
        st.session_state.text_color = "#333333"
        st.session_state.background_color = "#FFFFFF"
        st.session_state.accent_color = "#1D5B79"
        
    # Force page reload to apply changes
    st.rerun()


def filter_data(df: pd.DataFrame, selections: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter the DataFrame based on user selections.

    The filter criteria in the `selections` dictionary may include:
      - 'selected_license_plate': Filter by License Plate (if not "All").
      - 'selected_groups': Filter by a list of groups.
      - 'selected_dates': Filter by a single date or a date range.
      - 'selected_shift': Filter by shift (if not "All").
      - 'selected_events': Filter by a list of event types.
    
    Parameters:
        df (pd.DataFrame): The DataFrame to filter.
        selections (dict): A dictionary with filter criteria.
        
    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    filtered_df = df.copy()
    
    # Filter by license plate
    if selections.get("selected_license_plate") and selections["selected_license_plate"] != "All":
        filtered_df = filtered_df[filtered_df["License Plate"] == selections["selected_license_plate"]]
    
    # Filter by groups
    if selections.get("selected_groups") and len(selections["selected_groups"]) > 0:
        filtered_df = filtered_df[filtered_df["Group"].isin(selections["selected_groups"])]
    
    # Filter by date range
    if selections.get("selected_dates"):
        dates = selections["selected_dates"]
        if isinstance(dates, (list, tuple)) and len(dates) == 2:
            start_date, end_date = dates
            if "Shift Date" in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df["Shift Date"].dt.date >= start_date) & 
                    (filtered_df["Shift Date"].dt.date <= end_date)
                ]
    
    # Filter by shift
    if selections.get("selected_shift") and selections["selected_shift"] != "All":
        filtered_df = filtered_df[filtered_df["Shift"] == selections["selected_shift"]]
    
    # Filter by event types
    if selections.get("selected_events") and len(selections["selected_events"]) > 0:
        filtered_df = filtered_df[filtered_df["Event Type"].isin(selections["selected_events"])]
    
    return filtered_df


def get_shared_data() -> pd.DataFrame:
    """
    Get the shared DataFrame from session state or load it if not present.
    Returns a processed DataFrame ready for use.
    """
    if "df" not in st.session_state:
        df = load_data()
        if not df.empty:
            st.session_state.df = df
            return df
        return pd.DataFrame()
    return st.session_state.df

def clear_shared_data() -> None:
    """Clear the shared data from session state."""
    if "df" in st.session_state:
        del st.session_state.df

def refresh_data_if_needed() -> None:
    """Check if data needs to be refreshed and reload if necessary."""
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
        clear_shared_data()
    elif time.time() - st.session_state.last_refresh > 3600:  # Refresh every hour
        st.session_state.last_refresh = time.time()
        clear_shared_data()

def ensure_column_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure that certain columns are in the correct data type, especially after SQL queries."""
    if df.empty:
        return df
    
    # Convert date columns to datetime
    date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass  # Skip if conversion fails
    
    # Ensure numeric columns are numeric
    numeric_columns = ['Overspeeding Value', 'Speed', 'Top Speed', 'Speed Limit']
    for col in numeric_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass  # Skip if conversion fails
    
    # Ensure string columns are strings
    string_columns = ['Driver', 'Group', 'Shift', 'License Plate', 'Risk Level']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', '')
    
    # Add derived columns if they don't exist
    if 'Shift Date' in df.columns and 'Shift_Date_only' not in df.columns:
        df['Shift_Date_only'] = df['Shift Date'].dt.date
    
    return df

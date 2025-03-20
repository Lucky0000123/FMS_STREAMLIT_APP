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
    Process the input DataFrame with common transformations:
      - Convert date columns to datetime.
      - Replace missing numeric values with zero.
      - Calculate overspeeding values.
      - Assign risk levels based on overspeeding thresholds.
      - Ensure a 'Group' column exists by duplicating 'Fleet' if needed.
    
    Parameters:
        df (pd.DataFrame): The raw input DataFrame.
        
    Returns:
        pd.DataFrame: The processed DataFrame.
    """
    if df.empty:
        return df

    try:
        # Create a copy to avoid altering the original DataFrame
        processed_df = df.copy()

        # Convert specific columns to datetime
        for col in ['Shift Date', 'Date']:
            if col in processed_df.columns:
                processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce')

        # Fill missing numeric values with zero
        numeric_columns = processed_df.select_dtypes(include=[np.number]).columns
        processed_df[numeric_columns] = processed_df[numeric_columns].fillna(0)

        # Calculate overspeeding value if columns exist and apply new thresholds
        if 'Max Speed(Km/h)' in processed_df.columns and 'Speed Limit' in processed_df.columns:
            processed_df['Overspeeding Value'] = processed_df['Max Speed(Km/h)'] - processed_df['Speed Limit']
            # New thresholds for categorizing overspeeding
            processed_df['Overspeeding Category'] = pd.cut(
                processed_df['Overspeeding Value'],
                bins=[-float('inf'), 0, 5, 10, 15, float('inf')],
                labels=['None', 'Low', 'Moderate', 'High', 'Extreme']
            )

        # Assign risk levels based on overspeeding values
        processed_df = assign_risk_level(processed_df)

        # Update risk level assignment based on new overspeeding categories
        if 'Overspeeding Category' in processed_df.columns:
            processed_df['Risk Level'] = np.select(
                [
                    processed_df['Overspeeding Category'] == 'Extreme',
                    processed_df['Overspeeding Category'] == 'High',
                    processed_df['Overspeeding Category'] == 'Moderate',
                    processed_df['Overspeeding Category'] == 'Low',
                    processed_df['Overspeeding Category'] == 'None'
                ],
                ['Extreme', 'High', 'Medium', 'Low', 'None'],
                default='Medium'
            )

        # Create 'Group' column from 'Fleet' if missing
        if 'Group' not in processed_df.columns and 'Fleet' in processed_df.columns:
            processed_df['Group'] = processed_df['Fleet']
        
        return processed_df

    except Exception as e:
        logging.error(f"Error in data processing: {e}")
        st.error(f"Error processing data: {e}")
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
        conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};'
            f'SERVER=10.211.10.2;'
            f'DATABASE=FMS_DB;'
            f'UID=headofnickel;'
            f'PWD=Dataisbeautifulrev001!'
        )
        return conn
    except Exception as e:
        st.error(f"⚠️ SQL Connection Failed: {e}")
        logging.error(f"SQL Connection Error: {e}")
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
    <div class="header-container">
      <div class="header-text">
        <h1 class="header-title">{title}</h1>
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
        time.sleep(1.5)
        conn = get_sql_connection()
        if conn:
            try:
                query = "SELECT * FROM dbo.FMS_SPEED"
                df = pd.read_sql(query, conn)
                conn.close()
                return process_dataframe(df)  # Process the data before returning
            except Exception as e:
                st.error(f"⚠️ Failed to fetch SQL data: {e}")
                logging.error(f"SQL Query Error: {e}")
                return pd.DataFrame()
        else:
            return pd.DataFrame()


def load_data() -> pd.DataFrame:
    """Load data from an uploaded file or a default dataset."""
    DEFAULT_FILE_PATH = r"\\10.211.3.254\04. Mining\WBN - FLEET MANAGEMENT SYSTEM\Haulage DT Safety Event Report\FMS Event Data Query.xlsx"
    time.sleep(1.5)
    uploaded_file = st.session_state.get("uploaded_file")
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.session_state.using_default_data = False
            st.success("✅ Uploaded dataset is now being used!")
        except Exception as e:
            st.error(f"⚠️ Failed to read uploaded file: {e}")
            return pd.DataFrame()
    else:
        if os.path.exists(DEFAULT_FILE_PATH):
            df = pd.read_excel(DEFAULT_FILE_PATH)
            st.session_state.using_default_data = True
        else:
            st.error("⚠️ Default data file not found!")
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


def render_chart_title(translation_key: str):
    """Render a styled title for charts."""
    lang = st.session_state.language
    st.markdown(f"""
        <style>
            .chart-title-container {{
                background: linear-gradient(135deg, rgba(29, 91, 121, 0.1), rgba(46, 139, 87, 0.1));
                padding: 1.5rem;
                border-radius: 15px;
                margin: 1rem 0;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                transition: all 0.3s ease;
            }}
            .chart-title-container:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 25px rgba(0, 0, 0, 0.1);
            }}
            .chart-title {{
                font-size: 32px;
                font-weight: 800;
                background: linear-gradient(135deg, #1D5B79, #2E8B57);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                margin: 0;
                padding: 5px;
                letter-spacing: 1px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        </style>
        <div class="chart-title-container">
            <h2 class="chart-title">{TRANSLATIONS[lang][translation_key]}</h2>
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


def switch_theme() -> None:
    """
    Switch the dashboard theme by applying the appropriate CSS variables based on the current theme.

    The function reads the selected theme from the session state (defaulting to 'light' if not set)
    and forces an app rerun to apply the changes.
    """
    theme = st.session_state.get("theme", "light")
    theme_config = THEME_CONFIG.get(theme, THEME_CONFIG["light"])

    st.markdown(f"""
        <style>
        :root {{
            --primary-color: {theme_config['primary']};
            --secondary-color: {theme_config['secondary']};
            --accent-color: {theme_config['accent']};
            --background-color: {theme_config['background']};
            --text-color: {theme_config['text']};
            --border-color: {theme_config['border']};
        }}
        </style>
    """, unsafe_allow_html=True)

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

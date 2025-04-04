# Standard library imports
import streamlit as st
import time
import json
import platform
import pyodbc
import traceback

from sidebar import render_sidebar

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="Over Speeding Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from pathlib import Path
import tempfile
from datetime import datetime
from io import BytesIO
from streamlit_lottie import st_lottie
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from concurrent.futures import ThreadPoolExecutor

# Add the main folder to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Add SQL connection functionality
@st.cache_resource
def get_sql_connection():
    """Establish a connection to the SQL Server database."""
    try:
        # Connection parameters
        server = '10.211.10.2'
        database = 'FMS_DB'
        username = 'headofnickel'
        password = 'Dataisbeautifulrev001!'
        
        # Try different drivers in order of preference
        drivers = [
            '{ODBC Driver 18 for SQL Server}',
            '{ODBC Driver 17 for SQL Server}',
            '{SQL Server}'
        ]
        
        # Try each driver until one works
        for driver in drivers:
            try:
                # Create connection string
                conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
                
                # Establish connection
                conn = pyodbc.connect(conn_str)
                
                # Reset any previous error messages
                if "db_error" in st.session_state:
                    del st.session_state.db_error
                    
                return conn
            except pyodbc.Error:
                if driver == drivers[-1]:
                    # Don't raise if this is the last driver, just continue to exception handling
                    pass
                continue
                
    except Exception as e:
        # Store error message in session state but don't display it
        st.session_state.db_error = str(e)
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def run_sql_query(query, params=None):
    """Execute a SQL query and return results as a pandas DataFrame."""
    conn = None
    try:
        conn = get_sql_connection()
        if conn is None:
            # Don't show warnings to users, silently use local data
            return pd.DataFrame()
        
        # Execute query
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
            
        # Close connection as soon as data is retrieved
        conn.close()
        conn = None
        
        return df
    
    except pyodbc.ProgrammingError as e:
        # Silently handle "Attempt to use a closed connection" errors
        if "Attempt to use a closed connection" in str(e):
            try:
                # Try establishing a fresh connection
                conn = get_sql_connection()
                if conn:
                    if params:
                        df = pd.read_sql(query, conn, params=params)
                    else:
                        df = pd.read_sql(query, conn)
                    return df
            except Exception:
                # If still failing, return empty DataFrame without showing errors
                pass
        # Return empty DataFrame without showing error to user
        return pd.DataFrame()
    
    except Exception:
        # Silently handle all other errors - don't show errors to users
        return pd.DataFrame()
    
    finally:
        if conn is not None:
            try:
                conn.close()
            except:
                pass

# Local imports
from utils import (
    get_sql_connection,
    load_data,
    refresh_data_if_needed,
    load_lottieurl,
    get_translation,
    process_dataframe,
    assign_risk_level,
    render_chart_title,
    render_header,
    filter_data,
    get_shared_data,
    render_glow_line,
    ensure_column_types
)
from translations import get_event_translation
from config import (
    THEME_CONFIG,
    RISK_THRESHOLDS,
    UPLOAD_CONFIG,
    PDF_CONFIG,
    DB_CONFIG,
    GLOBAL_CSS
)

# Apply global CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Initialize session state
if "language" not in st.session_state:
    st.session_state.language = "EN"

# Get current language
lang = st.session_state["language"]

# Initialize group_fig_list
group_fig_list = []

# Add this function at the top of the file, after imports
def calculate_risk_level(speed_value):
    """Calculate risk level based on overspeeding value."""
    try:
        speed = float(speed_value)
        if speed >= 20:
            return 'Extreme'
        elif speed >= 10:
            return 'High'
        else:
            return 'Medium'
    except (ValueError, TypeError):
        return 'Medium'

# --------------------------------------------------------------------
# LANGUAGE TOGGLE AND ANIMATION
# --------------------------------------------------------------------
# Check if language was just changed
if "language_changed" in st.session_state and st.session_state.language_changed:
    st.session_state.language_changed = False  # Reset the flag
    # Force a rerun to apply the language change
    st.rerun()

# Create a row with two columns for the translation button and JSON animation
col_trans, col_json = st.columns([1, 1])

with col_trans:
    st.markdown("""
    <div style="
        padding: 10px;
        border-radius: 12px;
        margin-top: 10px;
        text-align: center;
        background: linear-gradient(to right, rgba(29, 91, 121, 0.05), transparent);
    ">
        <h3 style="
            color: #1D5B79;
            margin-bottom: 10px;
            font-size: 22px;
            font-weight: 600;
            letter-spacing: 0.5px;
        ">{}</h3>
    </div>
    """.format(get_translation("click_for_translation", lang)), unsafe_allow_html=True)
    
    translation_label = "切换中文" if lang == "EN" else "Switch to English"
    
    # Define a callback that sets a flag when language changes
    def change_language():
        new_lang = "ZH" if lang == "EN" else "EN"
        st.session_state.language = new_lang
        st.session_state.language_changed = True
    
    st.button(translation_label, on_click=change_language, key="lang_toggle_btn")

with col_json:
    try:
        # Load the animation JSON file using proper path resolution
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "ani15.json")
        with open(json_path, "r", encoding='utf-8') as f:
            animation_data = json.load(f)
        
        # Display the animation
        st_lottie(
            animation_data,
            speed=1,
            reverse=False,
            loop=True,
            quality="high",
            height=200
        )
    except Exception as e:
        st.warning(f"Animation could not be loaded. Error: {str(e)}")

# Add space after the row
st.markdown("<br>", unsafe_allow_html=True)
render_glow_line()
render_glow_line()

# Style and add the translation button
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 50px;
        background: linear-gradient(to right, #1D5B79, #2E8B57);
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 500;
        transition: all 0.3s ease;
        margin-top: 10px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Comprehensive styling for sliders */
    .stSlider {
        background: transparent !important;
    }
    .stSlider > div {
        background: transparent !important;
    }
    .stSlider > div > div {
        background: transparent !important;
    }
    [data-testid="stSlider"] {
        background: transparent !important;
    }
    
    /* Style slider thumb and track */
    .stSlider > div > div > div {
        background-color: #5F99AE !important;
    }
    
    /* Style the slider numbers */
    .stSlider [data-baseweb="slider"] [role="slider"] + div {
        font-weight: 700 !important;
        color: #333333 !important;
        font-size: 1.1rem !important;
    }
    
    /* Override slider range number styles */
    [data-testid="stSlider"] span {
        font-weight: 700 !important;
        color: #333333 !important;
        font-size: 1.1rem !important;
    }
    
    /* Remove any background from text below slider */
    [data-testid="stSlider"] + div {
        background: transparent !important;
    }
    div[style*='text-align: center; color: #666'] {
        font-weight: 700 !important;
        color: #333333 !important;
        font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Render header using utils function
render_header(get_translation("speeding_title", lang), "")

# After the header section, add the following CSS and content
st.markdown("""
<style>
    /* Global Font Settings for Better Multilingual Support */
    body, .stApp, .element-container, .stMarkdown, .stText, button, input, select, textarea {
        font-family: "Segoe UI", "Microsoft YaHei", "微软雅黑", "PingFang SC", "Hiragino Sans GB", sans-serif !important;
    }
    
    /* Ensure proper spacing and sizing for CJK characters */
    .chart-title, h1, h2, h3, h4, h5, h6, p, span, div, button {
        letter-spacing: normal !important;
        line-height: 1.6 !important;
    }
    
    /* Fix for Chinese text wrapping */
    .stMarkdown p, .stText p, button, .section-header, .rating-item span {
        word-break: normal !important;
        overflow-wrap: break-word !important;
    }
    
    /* Improve overall styling consistency */
    .pro-container {
        background: linear-gradient(135deg, #1D5B79, #2E8B57);  /* Updated gradient background */
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .pro-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
        background: linear-gradient(135deg, #1D5B79, #2E8B57);  /* Maintain gradient on hover */
    }
    
    /* Enhanced section headers for better visibility */
    .section-header {
        color: #FFFFFF;  /* White text for better contrast */
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        display: flex;
        align-items: center;
        gap: 10px;
        position: relative;
        overflow: hidden;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);  /* Text shadow for better readability */
    }
    
    .section-header:after {
        content: "";
        position: absolute;
        left: 0;
        bottom: 0;
        height: 2px;
        width: 60px;
        background: linear-gradient(to right, #FFFFFF, rgba(255, 255, 255, 0.3));
    }
    
    /* Improved rating items for better clarity */
    .rating-item {
        display: flex;
        align-items: center;
        padding: 15px;
        margin: 10px 0;
        background: rgba(255, 255, 255, 0.1);  /* Semi-transparent white background */
        border-radius: 10px;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .rating-item:hover {
        transform: translateX(5px);
        background: rgba(255, 255, 255, 0.15);  /* Slightly more opaque on hover */
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    
    .rating-item span {
        color: #FFFFFF;  /* White text for better contrast */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);  /* Text shadow for better readability */
    }
    
    /* Enhanced risk indicator dots */
    .speed-dot {
        min-width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 15px;
        position: relative;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Specific colors for risk levels */
    .speed-dot.medium {
        background-color: #FFD700;  /* Gold for medium risk */
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.7);
    }
    
    .speed-dot.high {
        background-color: #FFA500;  /* Orange for high risk */
        box-shadow: 0 0 8px rgba(255, 165, 0, 0.7);
    }
    
    .speed-dot.extreme {
        background-color: #FF0000;  /* Red for extreme risk */
        box-shadow: 0 0 8px rgba(255, 0, 0, 0.7);
    }
    
    /* Radio button styling */
    div[data-testid="stRadio"] label {
        background: rgba(255, 255, 255, 0.1) !important;  /* Semi-transparent white background */
        color: #FFFFFF !important;  /* White text */
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
    
    div[data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.2) !important;  /* Slightly more opaque on hover */
    }
    
    /* Slider styling */
    .stSlider {
        background: rgba(255, 255, 255, 0.1) !important;  /* Semi-transparent white background */
        padding: 10px !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    .stSlider [data-baseweb="slider"] span {
        color: #706D54 !important;  /* White text */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Date display styling */
    .date-display {
        background: rgba(29, 91, 121, 0.2);  /* Darker semi-transparent background */
        color: #FFFFFF;  /* White text */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);  /* Stronger text shadow */
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);  /* Add shadow for depth */
    }
    
    /* Date display specific styling */
    .date-display-days {
        font-size: 20px;  /* Slightly larger */
        font-weight: 700;  /* Bolder */
        color: #FFFFFF;  /* White */
        margin-bottom: 5px;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);  /* Enhanced shadow */
    }
    
    .date-display-range {
        font-size: 17px;  /* Slightly larger */
        color: #FFFFFF;  /* Solid white instead of transparent */
        font-weight: 600;  /* Semi-bold */
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);  /* Enhanced shadow */
    }
    
    /* Chart title styling - updated with darker gradient background */
    .chart-title {
        background: linear-gradient(135deg, rgba(29, 91, 121, 0.85), rgba(46, 139, 87, 0.85));  /* Darker gradient background */
        color: #FFFFFF;  /* White text */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);  /* Enhanced text shadow for better readability */
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);  /* Enhanced shadow for depth */
    }
    
    .chart-title h2 {
        margin: 0;
        font-size: 26px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Fleet group title styling to match main titles */
    .fleet-group-title {
        background: linear-gradient(135deg, rgba(29, 91, 121, 0.85), rgba(46, 139, 87, 0.85));
        color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    .fleet-group-title h2 {
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
        text-align: center;
        margin: 0;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
    }
    
    /* Additional styling enhancements to ensure consistent dark backgrounds */
    [data-chart] {
        background: linear-gradient(135deg, rgba(29, 91, 121, 0.85), rgba(46, 139, 87, 0.85)) !important;
    }
    
    /* Style slider thumb and track */
    .stSlider > div > div > div {
        background-color: #FFFFFF !important;
    }
    
    /* Style the slider numbers */
    .stSlider [data-baseweb="slider"] [role="slider"] + div {
        font-weight: 700 !important;
        color: #FFFFFF !important;
        font-size: 1.1rem !important;
    }
    
    /* Override slider range number styles */
    [data-testid="stSlider"] span {
        font-weight: 700 !important;
        color: #FFFFFF !important;
        font-size: 1.1rem !important;
    }
    
    /* Remove any background from text below slider */
    [data-testid="stSlider"] + div {
        background: transparent !important;
    }
    div[style*='text-align: center; color: #666'] {
        font-weight: 700 !important;
        color: #FFFFFF !important;
        font-size: 1.1rem !important;
    }
    
    /* Make radio buttons more visible against gradient */
    div[data-testid="stRadio"] div[role="radiogroup"] div:has(input[type="radio"]) {
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        margin: 5px 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Improve radio text visibility */
    div[data-testid="stRadio"] label span {
        color: #FFFFFF !important;
        font-weight: 500 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Create three columns for the filters
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown(f"""
    <div class="pro-container">
        <div class="section-header">
            <span>📊</span> {get_translation("overspeed_rating", lang)}
        </div>
        <div class="rating-item">
            <div class="speed-dot medium"></div>
            <span>{get_translation("speed_description_medium", lang)}</span>
        </div>
        <div class="rating-item">
            <div class="speed-dot high"></div>
            <span>{get_translation("speed_description_high", lang)}</span>
        </div>
        <div class="rating-item">
            <div class="speed-dot extreme"></div>
            <span>{get_translation("speed_description_extreme", lang)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="pro-container">
        <div class="section-header">
            <span>⏰</span> {get_translation("select_shift", lang)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    shift_type = st.radio(
        "",
        [
            get_translation("all_shifts", lang),
            get_translation("night_shift", lang),
            get_translation("morning_shift", lang)
        ],
        key="shift_selection",
        horizontal=False
    )

with col3:
    st.markdown(f"""
    <div class="pro-container">
        <div class="section-header">
            <span>📅</span> {get_translation("select_time_range", lang)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    trend_days = st.slider(
        "",
        min_value=7,
        max_value=30,
        value=7,
        key="trend_days"
    )
    
    # Calculate and display the actual date range
    if 'df' in st.session_state and not st.session_state.df.empty and 'Shift Date' in st.session_state.df.columns:
        try:
            df = st.session_state.df  # Get df from session state
            latest_date = df['Shift Date'].max()
            if pd.notna(latest_date):
                trend_end = latest_date
                trend_start = trend_end - pd.DateOffset(days=trend_days)
                
                # Format dates for display
                start_date_str = trend_start.strftime('%Y-%m-%d')
                end_date_str = trend_end.strftime('%Y-%m-%d')
                
                # Display days and date range with improved styling
                st.markdown(f"""
                <div class="date-display">
                    <div class="date-display-days dark-mode-compatible">{trend_days} {get_translation('days', lang)}</div>
                    <div class="date-display-range dark-mode-compatible">{start_date_str} → {end_date_str}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="date-display">
                    <div class="date-display-days">{trend_days} {get_translation('days', lang)}</div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div class="date-display">
                <div class="date-display-days">{trend_days} {get_translation('days', lang)}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="date-display">
            <div class="date-display-days">{trend_days} {get_translation('days', lang)}</div>
        </div>
        """, unsafe_allow_html=True)

# Create containers for loading states
loading_container = st.empty()
success_container = st.empty()

# -------------------- DATA LOADING --------------------
# Check if we can connect to SQL first
if "data_source" not in st.session_state:
    st.session_state.data_source = None  # Initialize

# Try to establish SQL connection if not already set
if st.session_state.data_source is None:
    # Show loading indicator
    sql_loading = st.empty()
    sql_loading.info("Checking data sources...")
    
    # Try to connect to SQL database
    conn = get_sql_connection()
    if conn is not None:
        # SQL connection successful
        st.session_state.data_source = "sql"
        sql_loading.success("Connected to SQL database!")
        time.sleep(1)
        sql_loading.empty()
    else:
        # SQL connection failed
        st.session_state.data_source = "local"
        sql_loading.warning("Could not connect to SQL database. Using local data.")
        time.sleep(1)
        sql_loading.empty()

# Check if we need to refresh data
refresh_data_if_needed()

# Load data based on the data source
if "df" not in st.session_state:
    # Create a loading message
    loading_container = st.empty()
    with loading_container:
        with st.spinner("Loading Data..."):
            # Create loading animation
            try:
                lottie_loading = load_lottieurl('https://assets2.lottiefiles.com/packages/lf20_poqmycwy.json')
                if lottie_loading is not None:
                    st_lottie(lottie_loading, height=200, key="loading_animation")
                else:
                    st.info("Please wait while we load the data...")
            except Exception as e:
                st.info("Please wait while we load the data...")
            st.info("Please wait while we load the data...")

    # First check if we have an uploaded file in session state
    if "uploaded_file" in st.session_state and st.session_state.uploaded_file is not None:
        try:
            df = pd.read_excel(st.session_state.uploaded_file)
            st.session_state.df = df
            st.session_state.data_source = "upload"
            loading_container.empty()
            success_container = st.empty()
            success_container.success("✅ Using uploaded dataset!")
            time.sleep(2)
            success_container.empty()
        except Exception as e:
            loading_container.warning(f"Could not use uploaded file: {str(e)}. Falling back to SQL database.")
            time.sleep(2)
            # Continue with SQL loading if uploaded file failed
    
    # If no uploaded file or it failed to load, try SQL or default data
    if "df" not in st.session_state:
        try:
            # Try to load using utils
            df = load_data()
            if not df.empty:
                st.session_state.df = df
                loading_container.empty()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.session_state.df = pd.DataFrame()

# Ensure df is properly defined by getting it from session state
if "df" in st.session_state:
    df = st.session_state.df
else:
    df = pd.DataFrame()  # Create an empty DataFrame as fallback

# Set default selections since we removed the sidebar filters
selections = {
    "selected_shift": "All",
    "selected_dates": None,
    "selected_license_plate": "All",
    "selected_groups": df["Group"].unique().tolist() if not df.empty and "Group" in df.columns else [],
    "selected_events": ["Speeding"]
}

# Store selections in session state for other components
st.session_state.selections = selections

# Process the data if needed
if not df.empty and 'Overspeeding Value' in df.columns:
    df = assign_risk_level(df)



# -------------------- SPEEDING EVENTS BY DAY --------------------
def render_enhanced_chart_title(translation_key):
    """Render an enhanced chart title with styling and animations."""
    try:
        # Get the translated text
        title_text = get_translation(translation_key, lang)
        
        # Render the enhanced chart title
        st.markdown(f"""
        <div class="chart-title" data-chart="{translation_key}" style="padding: 10px; margin: 10px 0;">
            <h2 style="font-size: 20px; margin: 0;">{title_text}</h2>
        </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback if something goes wrong
        st.markdown(f"""
        <div class="chart-title">
            <h2 style="font-size: 20px; margin: 0;">{translation_key}</h2>
        </div>
        """, unsafe_allow_html=True)

render_enhanced_chart_title("speeding_events_by_day")

# Ensure proper date conversion and handling
if 'Shift Date' in df.columns:
    try:
        # Get the date range from the data
        latest_date = df['Shift Date'].max()
        trend_end = latest_date
        trend_start = trend_end - pd.DateOffset(days=trend_days)
        
        # Filter data for the trend
        trend_df = df[
            (df['Shift Date'] >= trend_start) & 
            (df['Shift Date'] <= trend_end)
        ].copy()
        
        if 'Event Type' in trend_df.columns:
            trend_df = trend_df[trend_df['Event Type'] == 'Speeding'].copy()
            
            # Apply shift filter if selected
            if shift_type != get_translation("all_shifts", lang):
                # Get the original English values for shifts
                night_shift_value = "Malam" if "Malam" in trend_df["Shift"].unique() else "Night"
                morning_shift_value = "Siang" if "Siang" in trend_df["Shift"].unique() else "Day"
                
                # Map the translated selection back to the original value
                shift_value = night_shift_value if shift_type == get_translation("night_shift", lang) else morning_shift_value
                trend_df = trend_df[trend_df['Shift'] == shift_value]
            
            if not trend_df.empty:
                # Group the data
                trend_data = trend_df.groupby(
                    [pd.Grouper(key='Shift Date', freq='D'), 'Risk Level']
                ).size().unstack(fill_value=0).reset_index()
                
                # Ensure all risk levels are present
                for risk in ["Extreme", "High", "Medium"]:
                    if risk not in trend_data.columns:
                        trend_data[risk] = 0
                
                trend_data["Total Events"] = trend_data[["Extreme", "High", "Medium"]].sum(axis=1)
                
                # Create visualization
                risk_colors = {'Extreme': '#FF0000', 'High': '#FFA500', 'Medium': '#FFD700'}
                fig1 = px.line(
                    trend_data,
                    x="Shift Date",
                    y=trend_data.columns[1:-1],
                    labels={'value': 'Number of Events'},
                    color_discrete_map=risk_colors,
                    line_shape="linear",
                    template="plotly_white"
                )
                
                for i, trace in enumerate(fig1.data):
                    trace.update(
                        fill='tozeroy' if i == 0 else 'tonexty', 
                        opacity=0.1,
                        line=dict(width=3),
                        mode='lines+markers', 
                        marker=dict(size=8, line=dict(width=1, color='black'))
                    )
                
                fig1.update_traces(
                    hovertemplate="<b>📅 " + get_translation("date", lang) + ": %{x}</b><br>🔥 " + 
                                  get_translation("risk_level", lang) + ": %{fullData.name}<br>📊 " + 
                                  get_translation("number_of_events", lang) + ": %{y}",
                    hoverlabel=dict(bgcolor="white", font_size=13, font_color="black", font_family="Arial Black")
                )
                
                # Add total events annotations
                for i, date in enumerate(trend_data["Shift Date"]):
                    fig1.add_annotation(
                        x=date,
                        y=-5,
                        text=f" {trend_data['Total Events'][i]}",
                        showarrow=False,
                        font=dict(size=12, color="black"),
                        xshift=0,
                        yshift=-20
                    )
                
                fig1.update_layout(
                    height=400,
                    template="plotly_white",
                    title_text=get_translation("speeding_events_title", lang),
                    title_x=0.5,
                    title_font=dict(size=18, family="Arial", color="#2a3f5f"),
                    xaxis_title=get_translation("date", lang),
                    yaxis_title=get_translation("number_of_events", lang),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(
                        tickformat="%b %d, %Y", 
                        showgrid=True,
                        gridcolor='rgba(200, 200, 200, 0.5)', 
                        linecolor='black', 
                        linewidth=2
                    ),
                    yaxis=dict(
                        showgrid=True, 
                        gridcolor='rgba(200, 200, 200, 0.5)',
                        linecolor='black', 
                        linewidth=2
                    ),
                    legend=dict(
                        title=get_translation("risk_level", lang), 
                        orientation="h", 
                        yanchor="bottom", 
                        y=-0.3,
                        font=dict(size=12, color="black")
                    ),
                    margin=dict(l=20, r=20, t=40, b=80)
                )
                
                # Store the main figure in session state for PDF generation
                st.session_state["main_trend_fig"] = fig1

                # Display the chart
                st.plotly_chart(fig1, use_container_width=True, key="main_speeding_trend")
            else:
                st.warning(get_translation("no_data_warning", lang))
    except Exception as e:
            st.error(get_translation("data_processing_error", lang).format(error=str(e)))
    except Exception as e:
        st.error(f"Error processing data: {e}")
else:
    st.error(get_translation("column_not_found_error", lang).format(column="Shift Date"))


# -------------------- OVERSPEEDING INTENSITY BY GROUP --------------------
render_enhanced_chart_title("overspeeding_intensity")

# Define color schemes
bar_colors = {'Extreme': '#FF5733', 'High': '#FFA500', 'Medium': '#FFD700'}
trend_colors = {'Extreme': '#C70039', 'High': '#FF8C00', 'Medium': '#DAA520'}

if not trend_df.empty and 'Group' in trend_df.columns:
    fleet_groups = sorted(trend_df['Group'].unique())
    
    for idx, group in enumerate(fleet_groups):
        group_df = trend_df[trend_df["Group"] == group]
        
        if not group_df.empty:
            # Process group data
            processed_df = group_df.groupby(
                ["Shift Date", "Risk Level"]
            ).size().unstack(fill_value=0).reset_index()
            
            # Ensure all risk categories exist
            for risk in ["Extreme", "High", "Medium"]:
                if risk not in processed_df.columns:
                    processed_df[risk] = 0
            
            processed_df["Total Events"] = processed_df[["Extreme", "High", "Medium"]].sum(axis=1)
            
            # Create visualization
            fig = go.Figure()
            
            # First add all area traces in specific order: Medium, High, Extreme
            risk_order = ["Medium", "High", "Extreme"]  # Add lowest to highest for proper stacking
            for risk_level in risk_order:
                fig.add_trace(
                    go.Scatter(
                        x=processed_df["Shift Date"],
                        y=processed_df[risk_level],
                        name=risk_level,
                        fill='tozeroy',
                        mode='lines',
                        line=dict(color=bar_colors[risk_level], width=3),
                        opacity=0.85,
                        hovertemplate="<b>" + get_translation("date", lang) + ": %{x}</b><br>" + 
                                      get_translation("risk_level", lang) + ": %{fullData.name}<br>" + 
                                      get_translation("events", lang) + ": %{y}"
                    )
                )
            
            # Now add all line traces so they appear on top
            for risk_level in risk_order:  # Use same order for consistency
                fig.add_trace(
                    go.Scatter(
                        x=processed_df["Shift Date"],
                        y=processed_df[risk_level].rolling(window=3, min_periods=1).mean(),
                        mode='lines+markers',
                        name=f"{risk_level} {get_translation('trend', lang)}",
                        line=dict(color=trend_colors[risk_level], width=2.5, dash='solid'),
                        marker=dict(symbol='circle', size=8, color=trend_colors[risk_level]),
                        hovertemplate="<b>" + get_translation("date", lang) + ": %{x}</b><br>" + 
                                      get_translation("trend", lang) + ": %{y}"
                    )
                )

            # Add total events trend line last so it's on top of everything
            fig.add_trace(
                go.Scatter(
                    x=processed_df["Shift Date"],
                    y=processed_df["Total Events"].rolling(window=3, min_periods=1).mean(),
                    mode='lines+markers',
                    name=f"{get_translation('total_events', lang)} {get_translation('trend', lang)}",
                    line=dict(color='#1F77B4', width=3, dash='solid'),
                    marker=dict(symbol='circle', size=10, color='#1F77B4'),
                    hovertemplate="<b>" + get_translation("date", lang) + ": %{x}</b><br>" + 
                                  get_translation("total_events", lang) + " " + 
                                  get_translation("trend", lang) + ": %{y}"
                )
            )

            # Update layout
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=40, b=50),
                legend=dict(
                    title=get_translation("risk_level", lang),
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11, color="black")
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hoverlabel=dict(
                    bgcolor="black",
                    font_size=12,
                    font_color="white",
                    font_family="Arial"
                ),
                xaxis=dict(
                    tickformat="%b %d, %Y",
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.2)',
                    linecolor='black',
                    linewidth=2,
                    title=get_translation("date", lang)
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.2)',
                    linecolor='black',
                    linewidth=2,
                    title=get_translation("number_of_events", lang)
                )
            )

            # Display chart title and chart
            st.markdown(f"""
                <div class="fleet-group-title" style="padding: 10px; margin: 10px 0; background: rgba(29, 91, 121, 0.8); border-radius: 8px;">
                    <h2 style="font-size: 18px; margin: 0; color: #FFFFFF; text-align: center;">📊 {get_translation("fleet_group", lang)}: {group}</h2>
                </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, key=f"group_chart_{group}")
            group_fig_list.append(fig)
    
    # Store figures in session state
    st.session_state["group_fig_list"] = group_fig_list

else:
    st.warning(get_translation("no_overspeeding_data", lang))

@st.cache_data(ttl=300)
def get_speeding_metrics_sql(selections):
    """Get all speeding metrics in a single optimized query."""
    where_conditions = []
    
    if selections.get("dates"):
        if isinstance(selections["dates"], tuple):
            start_date, end_date = selections["dates"]
            where_conditions.append(f"[Shift Date] >= '{start_date}' AND [Shift Date] <= '{end_date}'")
        else:
            date_val = selections["dates"]
            where_conditions.append(f"CAST([Shift Date] AS DATE) = '{date_val}'")
    
    if selections.get("group", "All") != "All":
        where_conditions.append(f"[Group] = '{selections['group']}'")
    
    where_clause = " AND ".join(where_conditions)
    if where_clause:
        where_clause = f"WHERE {where_clause}"
    
    try:
        metrics_query = f"""
        WITH BaseStats AS (
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT [Driver]) as unique_drivers,
                AVG([Overspeeding Value]) as avg_overspeed,
                MAX([Overspeeding Value]) as max_overspeed,
                COUNT(CASE WHEN [Overspeeding Value] >= 20 THEN 1 END) as extreme_events,
                COUNT(CASE WHEN [Overspeeding Value] >= 10 AND [Overspeeding Value] < 20 THEN 1 END) as high_events,
                COUNT(CASE WHEN [Overspeeding Value] < 10 THEN 1 END) as medium_events
            FROM dbo.FMS_SPEED
            {where_clause}
        ),
        GroupStats AS (
            SELECT 
                [Group],
                COUNT(*) as group_events,
                AVG([Overspeeding Value]) as group_avg_speed
            FROM dbo.FMS_SPEED
            {where_clause}
            GROUP BY [Group]
        ),
        TopGroups AS (
            SELECT TOP 5
                [Group],
                group_events,
                group_avg_speed
            FROM GroupStats
            ORDER BY group_events DESC
        )
        SELECT 
            b.*,
            STRING_AGG(CONCAT(g.[Group], ' (', g.group_events, ')'), CHAR(13)) as top_groups
        FROM BaseStats b
        CROSS JOIN TopGroups g
        GROUP BY 
            b.total_events, b.unique_drivers, b.avg_overspeed,
            b.max_overspeed, b.extreme_events, b.high_events,
            b.medium_events
        """
        
        metrics_df = run_sql_query(metrics_query)
        if not metrics_df.empty:
            return {
                'total_events': metrics_df.iloc[0]['total_events'],
                'unique_drivers': metrics_df.iloc[0]['unique_drivers'],
                'avg_overspeed': round(metrics_df.iloc[0]['avg_overspeed'], 1),
                'max_overspeed': metrics_df.iloc[0]['max_overspeed'],
                'extreme_events': metrics_df.iloc[0]['extreme_events'],
                'high_events': metrics_df.iloc[0]['high_events'],
                'medium_events': metrics_df.iloc[0]['medium_events'],
                'top_groups': metrics_df.iloc[0]['top_groups'].split('\r') if metrics_df.iloc[0]['top_groups'] else []
            }
    except Exception as e:
        st.error(f"Error calculating speeding metrics: {e}")
        return None

@st.cache_data(ttl=300)
def get_speeding_trend_data_sql(selections):
    """Get speeding trend data with optimized SQL query."""
    where_conditions = []
    
    if selections.get("dates"):
        if isinstance(selections["dates"], tuple):
            start_date, end_date = selections["dates"]
            where_conditions.append(f"[Shift Date] >= '{start_date}' AND [Shift Date] <= '{end_date}'")
        else:
            date_val = selections["dates"]
            where_conditions.append(f"CAST([Shift Date] AS DATE) = '{date_val}'")
    
    if selections.get("group", "All") != "All":
        where_conditions.append(f"[Group] = '{selections['group']}'")
    
    where_clause = " AND ".join(where_conditions)
    if where_clause:
        where_clause = f"WHERE {where_clause}"
    
    try:
        trend_query = f"""
        WITH DateRange AS (
            SELECT TOP {trend_days}
                CAST([Shift Date] AS DATE) as event_date,
                COUNT(*) as total_events,
                AVG([Overspeeding Value]) as avg_overspeed,
                COUNT(CASE WHEN [Overspeeding Value] >= 20 THEN 1 END) as extreme_events
            FROM dbo.FMS_SPEED
            {where_clause}
            GROUP BY CAST([Shift Date] AS DATE)
            ORDER BY event_date DESC
        )
        SELECT *
        FROM DateRange
        ORDER BY event_date ASC
        """
        
        return run_sql_query(trend_query)
    except Exception as e:
        st.error(f"Error getting trend data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_group_stats_sql(selections):
    """Get group statistics using SQL."""
    where_conditions = []
    
    if selections.get("dates"):
        if isinstance(selections["dates"], tuple):
            start_date, end_date = selections["dates"]
            where_conditions.append(f"[Shift Date] >= '{start_date}' AND [Shift Date] <= '{end_date}'")
        else:
            date_val = selections["dates"]
            where_conditions.append(f"CAST([Shift Date] AS DATE) = '{date_val}'")
    
    where_clause = " AND ".join(where_conditions)
    if where_clause:
        where_clause = f"WHERE {where_clause}"
    
    try:
        group_query = f"""
        SELECT 
            [Group],
            COUNT(*) as total_events,
            AVG([Overspeeding Value]) as avg_overspeed,
            COUNT(CASE WHEN [Overspeeding Value] >= 20 THEN 1 END) as extreme_events,
            COUNT(DISTINCT [Driver]) as unique_drivers
        FROM dbo.FMS_SPEED
        {where_clause}
        GROUP BY [Group]
        ORDER BY total_events DESC
        """
        
        return run_sql_query(group_query)
    except Exception as e:
        st.error(f"Error getting group stats: {e}")
        return pd.DataFrame()
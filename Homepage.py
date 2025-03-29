"""
Complete Rewritten Homepage Code for FMS Safety Dashboard
with Dynamic Sidebar Theme Switching
"""

import os
import sys
import json
import time
import tempfile
import shutil
import warnings
import random
from datetime import datetime, timedelta, date
from pathlib import Path
from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import pyodbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import geopandas as gpd
import leafmap.foliumap as leafmap
from streamlit_lottie import st_lottie
import folium
from folium.plugins import MarkerCluster, HeatMap

# Local imports (make sure these modules exist in your project)
from utils import (
    process_dataframe,
    assign_risk_level as assign_risk_level_util,
    load_lottie_json as load_lottie_json_util,
    render_chart_title,
    render_header as render_header_util,
    filter_data as filter_data_util,
    render_glow_line as render_glow_line_util,
    get_shared_data,
    refresh_data_if_needed
)
from translations import TRANSLATIONS, get_translation
from config import (
    THEME_CONFIG,
    RISK_THRESHOLDS,
    UPLOAD_CONFIG,
    PDF_CONFIG,
    DB_CONFIG,
    GLOBAL_CSS
)
from pdf_generator import generate_report, generate_dashboard_report

# ------------------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="FMS Safety Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# Global CSS Injection (from your GLOBAL_CSS config)
# ------------------------------------------------------------------------------
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Session State Defaults
# ------------------------------------------------------------------------------
if "using_default_data" not in st.session_state:
    st.session_state.using_default_data = True
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "language" not in st.session_state:
    st.session_state.language = "EN"
if "theme" not in st.session_state:
    st.session_state.theme = "light"
    st.session_state.text_color = "#333333"
    st.session_state.background_color = "#FFFFFF"
    st.session_state.accent_color = "#1D5B79"
if "rerun_triggered" not in st.session_state:
    st.session_state.rerun_triggered = False
if "current_section" not in st.session_state:
    st.session_state.current_section = "analytics"
if "map_data_loaded" not in st.session_state:
    st.session_state.map_data_loaded = False
if "preloaded_map_df" not in st.session_state:
    st.session_state.preloaded_map_df = None
if "preloaded_map_df_heat" not in st.session_state:
    st.session_state.preloaded_map_df_heat = None

# ------------------------------------------------------------------------------
# Translation Dictionaries
# ------------------------------------------------------------------------------
group_translation = {
    "RIM": "RIM",
    "RIM-A": "RIM-A",
    "Group A": "A组",
    "Group B": "B组",
    "Group C": "C组"
}
event_translation = {
    "Look Around": "环顾四周",
    "Closed Eyes": "闭眼",
    "Phone": "手机",
    "Yawn": "打哈欠",
    "Smoking": "抽烟",
    "Bow Head": "低头",
    "Speeding": "超速",
    "Occlusion": "遮挡",
    "PCW": "行人碰撞预警",
    "FCW": "前碰撞预警",
    "Tired": "疲劳驾驶",
    "Overspeed warning in the area": "区域超速预警",
    "Short Following Distance": "跟车距离过近"
}

# ------------------------------------------------------------------------------
# Theme Configuration & Switch Function
# ------------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIGHT_THEME = os.path.join(BASE_DIR, "config_light.toml")
DARK_THEME = os.path.join(BASE_DIR, "config_dark.toml")
CONFIG_DIR = os.path.join(BASE_DIR, ".streamlit")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.toml")
os.makedirs(CONFIG_DIR, exist_ok=True)

def switch_theme():
    """Switch the theme by copying the corresponding config file and rerunning the app."""
    theme_file = LIGHT_THEME if st.session_state.theme == "light" else DARK_THEME
    if os.path.exists(theme_file):
        shutil.copy(theme_file, CONFIG_FILE)
        st.rerun()
    else:
        st.error(f"⚠️ Theme file missing: {theme_file}")

# ------------------------------------------------------------------------------
# Dynamic Sidebar CSS Injection Function
# ------------------------------------------------------------------------------
def inject_sidebar_theme_css():
    """Inject dynamic CSS for the sidebar based on the current theme."""
    theme = st.session_state.get("theme", "light")
    if theme == "dark":
        sidebar_bg    = "#121212"
        sidebar_text  = "#FFFFFF"
        button_bg     = "linear-gradient(145deg, #3A95FF, #4DA9FF)"
        button_hover  = "#5DAFFF"
        button_text   = "#FFFFFF"
        border_color  = "#2E2E2E"
        section_bg    = "rgba(40, 40, 40, 0.9)"
        header_border = "#3A95FF"
        divider_color = "#444444"
    else:
        sidebar_bg    = "#F8F8F8"
        sidebar_text  = "#2E3440"
        button_bg     = "linear-gradient(145deg, #1D5B79, #468B97)"
        button_hover  = "#468B97"
        button_text   = "#FFFFFF"
        border_color  = "#D3D3D3"
        section_bg    = "rgba(240, 240, 240, 0.95)"
        header_border = "#1D5B79"
        divider_color = "#D3D3D3"

    custom_css = f"""
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        color: {sidebar_text} !important;
        padding: 1rem;
        border-right: 1px solid {border_color};
    }}
    /* Sidebar Logo */
    .sidebar-logo {{
        text-align: center;
        margin-bottom: 20px;
        padding: 10px;
        border-bottom: 1px solid {divider_color};
    }}
    /* Custom Button Styling */
    .stButton>button {{
        background: {button_bg} !important;
        color: {button_text} !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        margin: 5px 0 !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1) !important;
    }}
    .stButton>button:hover {{
        background: {button_hover} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2) !important;
    }}
    /* Sidebar Sections */
    .sidebar-section {{
        background: {section_bg};
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 2px solid {border_color} !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease-in-out;
    }}
    .sidebar-section:hover {{
        transform: scale(1.02);
        box-shadow: 0px 6px 12px rgba(0,0,0,0.2);
    }}
    /* Sidebar Headers */
    .sidebar-header {{
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 8px;
        color: {sidebar_text} !important;
        border-bottom: 2px solid {header_border} !important;
        padding-bottom: 5px;
        letter-spacing: 1px;
    }}
    /* Selection Indicator */
    .selection-indicator {{
        background: linear-gradient(90deg, {divider_color}, transparent);
        border-left: 3px solid {header_border};
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 0 5px 5px 0;
        font-size: 0.9rem;
        font-weight: 500;
        color: {sidebar_text} !important;
    }}
    """
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SQL Connection Functions
# ------------------------------------------------------------------------------
@st.cache_resource
def get_sql_connection():
    """Establish a connection to the SQL Server database with enhanced error handling."""
    try:
        server = os.getenv('SQL_SERVER', '10.211.10.2')
        database = os.getenv('SQL_DATABASE', 'FMS_DB')
        username = os.getenv('SQL_USERNAME', 'headofnickel')
        password = os.getenv('SQL_PASSWORD', 'Dataisbeautifulrev001!')
        
        drivers = [
            '{ODBC Driver 18 for SQL Server}',
            '{ODBC Driver 17 for SQL Server}',
            '{SQL Server}'
        ]
        
        for driver in drivers:
            try:
                conn_str = (
                    f'DRIVER={driver};'
                    f'SERVER={server};'
                    f'DATABASE={database};'
                    f'UID={username};'
                    f'PWD={password};'
                    'Trusted_Connection=no;'
                    'Encrypt=no;'
                    'TrustServerCertificate=yes;'
                    'Connection Timeout=30;'
                    'Network Library=DBMSSOCN;'
                    'MultiSubnetFailover=yes;'
                    'ApplicationIntent=ReadWrite;'
                    'MultipleActiveResultSets=True;'
                    'Packet Size=4096;'
                    'ConnectRetryCount=5;'
                    'ConnectRetryInterval=10;'
                    'Pooling=true;'
                    'Max Pool Size=100;'
                    'Min Pool Size=0'
                )
                
                # Log connection attempt
                print(f"Attempting connection with driver: {driver}")
                
                max_retries = 5
                retry_delays = [2, 5, 10, 15, 30]
                
                for attempt, delay in enumerate(retry_delays, 1):
                    try:
                        conn = pyodbc.connect(conn_str, timeout=30)
                        cursor = conn.cursor()
                        cursor.execute("SELECT @@version")
                        version = cursor.fetchone()[0]
                        print(f"Connected successfully. SQL Server version: {version}")
                        cursor.close()
                        return conn
                    except pyodbc.Error as e:
                        print(f"Connection attempt {attempt} failed: {str(e)}")
                        if attempt < max_retries:
                            print(f"Retrying in {delay} seconds...")
                            time.sleep(delay)
                            continue
                        else:
                            print("Max retries reached, trying next driver...")
                            break
            except pyodbc.Error as e:
                print(f"Driver {driver} failed: {str(e)}")
                continue
        
        raise Exception("All connection attempts failed")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Database connection error: {error_msg}")
        st.session_state.db_error = {
            'message': error_msg,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    return None

@st.cache_data(ttl=300)
def run_sql_query(query, params=None):
    """Execute a SQL query and return results as a pandas DataFrame."""
    conn = None
    try:
        conn = get_sql_connection()
        if conn is None:
            return pd.DataFrame()
        if "SELECT" in query.upper() and "WITH" not in query.upper():
            query = query.rstrip()
            if query.endswith(";"):
                query = query[:-1]
            query += """
                OPTION (
                    RECOMPILE,
                    OPTIMIZE FOR UNKNOWN,
                    FAST 50,
                    USE HINT('ENABLE_PARALLEL_PLAN_PREFERENCE')
                );
            """
        try:
            if params:
                df = pd.read_sql(query, conn, params=params)
            else:
                df = pd.read_sql(query, conn)
            return df.copy()
        except Exception:
            return pd.DataFrame()
        finally:
            if conn is not None:
                conn.close()
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")
        return pd.DataFrame()

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def load_lottie_json(json_path: str):
    """Load a Lottie animation JSON file."""
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(f"⚠️ Animation file not found: {json_path}")
    except json.JSONDecodeError as e:
        st.error(f"⚠️ Invalid JSON format in {json_path}: {e}")
    return None

def assign_risk_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign a 'Risk Level' based on 'Overspeeding Value':
      - Extreme: >= 20
      - High: 10 to <20
      - Medium: <10
    """
    if "Overspeeding Value" in df.columns:
        conditions = [
            df["Overspeeding Value"] >= 20,
            (df["Overspeeding Value"] >= 10) & (df["Overspeeding Value"] < 20),
            df["Overspeeding Value"] < 10
        ]
        choices = ["Extreme", "High", "Medium"]
        df["Risk Level"] = np.select(conditions, choices, default="Medium")
    else:
        df["Risk Level"] = "Medium"
    return df

@st.cache_data
def load_data():
    """Load data from an uploaded file or a SQL database."""
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
        try:
            sql_query = """
                SELECT * FROM dbo.FMS_SPEED
                ORDER BY [Shift Date] DESC
            """
            df = run_sql_query(sql_query)
            if df.empty:
                st.warning("⚠️ No data returned from SQL query. Trying default file.")
                DEFAULT_FILE_PATH = r"\\10.211.3.254\04. Mining\WBN - FLEET MANAGEMENT SYSTEM\Haulage DT Safety Event Report\FMS Event Data Query.xlsx"
                if os.path.exists(DEFAULT_FILE_PATH):
                    df = pd.read_excel(DEFAULT_FILE_PATH)
                    st.session_state.using_default_data = True
                    st.info("ℹ️ Using default dataset.")
                else:
                    st.error("⚠️ Default data file not found!")
                    return pd.DataFrame()
            else:
                st.session_state.using_default_data = False
                st.session_state.data_source = "sql"
                st.info("ℹ️ Using SQL database.")
        except Exception as e:
            st.error(f"⚠️ Failed to connect to SQL database: {e}")
            DEFAULT_FILE_PATH = r"\\10.211.3.254\04. Mining\WBN - FLEET MANAGEMENT SYSTEM\Haulage DT Safety Event Report\FMS Event Data Query.xlsx"
            if os.path.exists(DEFAULT_FILE_PATH):
                df = pd.read_excel(DEFAULT_FILE_PATH)
                st.session_state.using_default_data = True
                st.info("ℹ️ Using default dataset as fallback.")
            else:
                st.error("⚠️ Default data file not found!")
                return pd.DataFrame()
    if "Shift Date" in df.columns:
        df["Shift Date"] = pd.to_datetime(df["Shift Date"], errors="coerce")
        df.dropna(subset=["Shift Date"], inplace=True)
        df["Date"] = df["Shift Date"].dt.date
        if "Shift" in df.columns:
            df["Shift"] = df["Shift"].str.capitalize()
    return df

def read_uploaded_geospatial_file(uploaded_file) -> gpd.GeoDataFrame:
    """Save an uploaded geospatial file to a temporary file and return a GeoDataFrame."""
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp.flush()
        tmp_path = tmp.name
    try:
        gdf = gpd.read_file(tmp_path)
    finally:
        os.unlink(tmp_path)
    return gdf

# ------------------------------------------------------------------------------
# Sidebar Rendering with New Dynamic Theme Updates
# ------------------------------------------------------------------------------
def render_sidebar(df: pd.DataFrame) -> dict:
    """
    Renders the sidebar for the dashboard and returns the user's filter selections.
    """
    # Inject dynamic sidebar CSS based on current theme
    inject_sidebar_theme_css()
    ASSETS_DIR = Path(__file__).parent / "assets"
    with st.sidebar:
        # 1) LOGO
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            st.markdown(
                """
                <style>
                .logo-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 0.5rem;
                    margin-bottom: 1rem;
                    border-radius: 10px;
                    background: none;
                }
                </style>
                <div class="logo-container">
                """, unsafe_allow_html=True)
            # Display logo without extra columns
            st.image(str(logo_path), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        # 2) THEME SELECTION
        st.markdown('<div class="section-title theme"><span>🎨 Theme Selection</span></div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌞 Light", key="light_theme", use_container_width=True):
                st.session_state.theme = "light"
                switch_theme()
        with col2:
            if st.button("🌙 Dark", key="dark_theme", use_container_width=True):
                st.session_state.theme = "dark"
                switch_theme()
        st.markdown(f'<div class="selection-indicator theme-indicator">Current Theme: {st.session_state.theme.capitalize()}</div>', unsafe_allow_html=True)
        # 3) LANGUAGE SELECTION
        st.markdown('<div class="section-title language"><span>🌍 Language Settings</span></div>', unsafe_allow_html=True)
        col_lang1, col_lang2 = st.columns(2)
        with col_lang1:
            if st.button("🇬🇧 English", key="english_lang", use_container_width=True):
                st.session_state.language = "EN"
                st.session_state.language_changed = True
                st.rerun()
        with col_lang2:
            if st.button("🇨🇳 中文", key="chinese_lang", use_container_width=True):
                st.session_state.language = "ZH"
                st.session_state.language_changed = True
                st.rerun()
        current_language = "English" if st.session_state.language == "EN" else "中文"
        st.markdown(f'<div class="selection-indicator language-indicator">Current Language: {current_language}</div>', unsafe_allow_html=True)
        # 4) DATE RANGE SELECTION
        st.markdown('<div class="sidebar-header">📅 Select Date Range</div>', unsafe_allow_html=True)
        if not df.empty and "Shift Date" in df.columns:
            min_date = df["Shift Date"].min().date()
            max_date = df["Shift Date"].max().date()
        else:
            min_date = date.today() - timedelta(days=30)
            max_date = date.today()
        col_dt1, col_dt2, col_dt3 = st.columns(3)
        with col_dt1:
            if st.button("📅 This Week", key="this_week", use_container_width=True):
                end_date = max_date
                start_of_week = end_date - timedelta(days=end_date.weekday())
                st.session_state.date_range = (max(min_date, start_of_week), end_date)
                st.rerun()
        with col_dt2:
            if st.button("📅 This Month", key="this_month", use_container_width=True):
                end_date = max_date
                start_of_month = end_date.replace(day=1)
                st.session_state.date_range = (max(min_date, start_of_month), end_date)
                st.rerun()
        with col_dt3:
            if st.button("📅 All Data", key="all_data", use_container_width=True):
                st.session_state.date_range = (min_date, max_date)
                st.rerun()
        default_range = st.session_state.get("date_range", (min_date, max_date))
        st.markdown('<div class="sidebar-subheader">Start Date:</div>', unsafe_allow_html=True)
        start_date = st.date_input("Select Start Date", value=default_range[0], min_value=min_date, max_value=max_date, key="start_date_input")
        st.markdown('<div class="sidebar-subheader">End Date:</div>', unsafe_allow_html=True)
        end_date = st.date_input("Select End Date", value=default_range[1], min_value=min_date, max_value=max_date, key="end_date_input")
        if start_date > end_date:
            st.warning("Start date cannot be after end date. Resetting to default.")
            start_date, end_date = default_range
        st.session_state.date_range = (start_date, end_date)
        st.markdown(f'<div class="selection-indicator">Selected: {start_date.strftime("%b %d")} - {end_date.strftime("%b %d, %Y")}</div>', unsafe_allow_html=True)
        # 5) SHIFT SELECTION
        st.markdown('<div class="section-title shift"><span>⏰ Shift Filter</span></div>', unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns(3)
        if "selected_shift" not in st.session_state:
            st.session_state.selected_shift = "All"
        with col_s1:
            if st.button("🌅 All", key="shift_all", use_container_width=True):
                st.session_state.selected_shift = "All"
        with col_s2:
            if st.button("☀️ Day", key="shift_day", use_container_width=True):
                st.session_state.selected_shift = "Siang"
        with col_s3:
            if st.button("🌙 Night", key="shift_night", use_container_width=True):
                st.session_state.selected_shift = "Malam"
        st.markdown(f'<div class="selection-indicator">Selected: {st.session_state.selected_shift}</div>', unsafe_allow_html=True)
        # 6) LICENSE PLATE SELECTION
        st.markdown('<div class="section-title vehicle"><span>🚛 Vehicle Selection</span></div>', unsafe_allow_html=True)
        license_plates = ["All"]
        if not df.empty and "License Plate" in df.columns:
            license_plates += sorted(df["License Plate"].unique())
        selected_plate = st.selectbox("Select License Plate", license_plates, label_visibility="collapsed")
        if selected_plate != "All":
            st.markdown(f'<div class="selection-indicator">Selected: {selected_plate}</div>', unsafe_allow_html=True)
        # 7) FLEET GROUP SELECTION
        st.markdown('<div class="section-title fleet"><span>🚜 Fleet Groups</span></div>', unsafe_allow_html=True)
        groups_list = []
        if not df.empty and "Group" in df.columns:
            groups_list = sorted(df["Group"].unique())
        selected_groups = st.multiselect("Select Fleet Group", options=groups_list, default=groups_list, label_visibility="collapsed")
        # 8) EVENT TYPES SELECTION
        st.markdown('<div class="section-title event"><span>⚠️ Event Categories</span></div>', unsafe_allow_html=True)
        default_events = ["Smoking", "Speeding", "Closed Eyes", "Phone", "Yawn"]
        all_events = []
        if not df.empty and "Event Type" in df.columns:
            all_events = sorted(df["Event Type"].unique())
        default_events = [evt for evt in default_events if evt in all_events]
        other_events = [evt for evt in all_events if evt not in default_events]
        final_event_list = default_events + other_events
        selected_events = st.multiselect("Select Event Types", options=final_event_list, default=default_events, label_visibility="collapsed")
    return {
        "selected_dates": st.session_state.date_range,
        "selected_shift": st.session_state.selected_shift,
        "selected_license_plate": selected_plate,
        "selected_groups": selected_groups,
        "selected_events": selected_events
    }

def filter_data(df: pd.DataFrame, selections: dict) -> pd.DataFrame:
    """Filter dataframe based on sidebar selections."""
    if df.empty:
        return df
    filtered_df = df.copy()
    if "selected_dates" in selections and selections["selected_dates"]:
        start_date, end_date = selections["selected_dates"]
        date_column = "Shift Date" if "Shift Date" in filtered_df.columns else None
        if date_column:
            if not pd.api.types.is_datetime64_any_dtype(filtered_df[date_column]):
                filtered_df[date_column] = pd.to_datetime(filtered_df[date_column])
            filtered_df = filtered_df[(filtered_df[date_column].dt.date >= start_date) & 
                                      (filtered_df[date_column].dt.date <= end_date)]
    if "selected_license_plate" in selections and selections["selected_license_plate"] != "All":
        filtered_df = filtered_df[filtered_df["License Plate"] == selections["selected_license_plate"]]
    if "selected_groups" in selections and selections["selected_groups"]:
        filtered_df = filtered_df[filtered_df["Group"].isin(selections["selected_groups"])]
    if "selected_shift" in selections and selections["selected_shift"] != "All":
        filtered_df = filtered_df[filtered_df["Shift"] == selections["selected_shift"]]
    if "selected_events" in selections and selections["selected_events"]:
        filtered_df = filtered_df[filtered_df["Event Type"].isin(selections["selected_events"])]
    return filtered_df

def render_glow_line():
    """Creates a visually appealing separator."""
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

def render_pulse_line():
    """Creates an animated pulsing separator."""
    st.markdown(
        """
        <style>
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.05); opacity: 0.8; }
                100% { transform: scale(1); opacity: 1; }
            }
            .pulse-divider {
                height: 6px;
                background: linear-gradient(90deg, #F24C3D, #1D5B79);
                box-shadow: 0 0 12px rgba(242, 76, 61, 0.6);
                animation: pulse 1.8s infinite ease-in-out;
                margin: 25px 0;
                border-radius: 5px;
            }
        </style>
        <div class="pulse-divider"></div>
        """,
        unsafe_allow_html=True
    )

def render_header():
    """Render header with title, logo, animation, and file upload."""
    lang = st.session_state.language
    if "language_changed" in st.session_state and st.session_state.language_changed:
        st.session_state.language_changed = False
    title = TRANSLATIONS[lang]["dashboard_title"]
    st.markdown(
        """
        <style>
            .title-text {
                font-family: 'Poppins', sans-serif;
                font-size: 48px;
                font-weight: 800;
                color: #2a3f5f;
                line-height: 1.2;
                white-space: nowrap;
                overflow-x: auto;
                padding-bottom: 10px;
            }
            .title-text::-webkit-scrollbar {
                height: 4px;
            }
            .title-text::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 2px;
            }
            .title-text::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 2px;
            }
            .title-text::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
            .title-highlight {
                background: linear-gradient(to right, #1D5B79, #F24C3D);
                -webkit-background-clip: text;
                color: transparent;
            }
            .glow-divider {
                height: 5px;
                background: linear-gradient(90deg, #ff8c42, #2a3f5f);
                box-shadow: 0 0 10px rgba(255, 140, 66, 0.8);
                margin: 25px 0;
                border-radius: 5px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    col1, col3 = st.columns([4.3, 1.2])
    with col1:
        ASSETS_DIR = Path("assets")
        safety_logo_path = ASSETS_DIR / "safety_logo.png"
        if safety_logo_path.exists():
            st.image(str(safety_logo_path), width=120)
        st.markdown(
            f"""
            <div class="title-text">
                <span class="title-highlight">{title}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        lottie_animation = load_lottie_json("assets/ani1.json")
        if lottie_animation:
            st_lottie(lottie_animation, speed=1, width=230, height=180, key="dashboard_animation")
    render_glow_line()

def render_file_upload():
    """Render file upload section."""
    st.markdown("📁 **Upload Your Dataset (Excel) / Wait for SQL Dataset**")
    uploaded_file = st.file_uploader("Drag and drop file here", type=["xlsx"], help="Limit 200MB per file • XLSX", key="file_upload_key")
    if uploaded_file is not None:
        current_file_name = getattr(st.session_state.get('uploaded_file'), 'name', None)
        if current_file_name != uploaded_file.name or not st.session_state.get('pending_upload', False):
            st.session_state.uploaded_file = uploaded_file
            st.session_state.using_default_data = False
            progress_container = st.empty()
            with progress_container:
                progress_bar = st.progress(0)
                st.write("Processing uploaded file...")
            try:
                with st.spinner("Validating Excel file..."):
                    progress_bar.progress(25)
                    test_df = pd.read_excel(uploaded_file, nrows=5)
                    progress_bar.progress(50)
                    uploaded_file.seek(0)
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    progress_container.empty()
                    st.success("✅ File uploaded successfully! Click 'Refresh Data' to use your dataset.")
                    st.session_state.data_needs_refresh = True
                    st.session_state.pending_upload = True
            except Exception as e:
                progress_container.empty()
                st.error(f"⚠️ Failed to read uploaded file: {e}")
                st.session_state.uploaded_file = None
    else:
        if 'uploaded_file' in st.session_state:
            del st.session_state.uploaded_file
            if 'pending_upload' in st.session_state:
                del st.session_state.pending_upload
        st.session_state.using_default_data = True

def render_kpis(filtered_df: pd.DataFrame):
    """Calculate and display Key Performance Indicators."""
    lang = st.session_state.language

    total_safety_events = len(filtered_df)
    total_speeding_events = len(filtered_df[filtered_df['Event Type'] == 'Speeding']) if "Event Type" in filtered_df.columns else 0
    extreme_risk_events = len(filtered_df[filtered_df['Risk Level'] == 'Extreme']) if "Risk Level" in filtered_df.columns else 0

    if "Max Speed(Km/h)" in filtered_df.columns and not filtered_df.empty:
        valid_speeds = filtered_df['Max Speed(Km/h)'][pd.notna(filtered_df['Max Speed(Km/h)'])]
        average_speed = valid_speeds.mean().round(1) if not valid_speeds.empty else 0
    else:
        average_speed = 0

    if "Overspeeding Value" in filtered_df.columns and not filtered_df.empty:
        valid_overspeeds = filtered_df['Overspeeding Value'][pd.notna(filtered_df['Overspeeding Value'])]
        average_overspeed = valid_overspeeds.mean().round(1) if not valid_overspeeds.empty else 0
    else:
        average_overspeed = 0

    if "Driver" in filtered_df.columns:
        # Filter out drivers with empty names before getting top offenders
        valid_drivers_df = filtered_df[filtered_df['Driver'].notna() & (filtered_df['Driver'].str.strip() != '')]
        top_offenders_series = valid_drivers_df['Driver'].value_counts().head(5)
        top_offenders = "<br>".join(f"{name} ({count})" for name, count in top_offenders_series.items())
    else:
        top_offenders = "N/A"

    if "Group" in filtered_df.columns and not filtered_df.empty:
        top_group = filtered_df['Group'].value_counts().idxmax()
        top_group_count = filtered_df['Group'].value_counts().max()
    else:
        top_group, top_group_count = "N/A", 0

    st.markdown(
        """
        <style>
            @keyframes float {
                0% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
                100% { transform: translateY(0px); }
            }
            
            @keyframes particle {
                0% { transform: translate(0, 0) scale(1); opacity: 0; }
                50% { opacity: 1; }
                100% { transform: translate(var(--tx), var(--ty)) scale(0); opacity: 0; }
            }

            .kpi-card {
                background: linear-gradient(145deg, #1c2b3a, #23374d);
                border-radius: 15px;
                padding: 20px;
                margin: 10px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
                border: 1px solid rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
                z-index: 1;
            }

            .kpi-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(125deg, #2c3e50, #1a5276, #154360);
                opacity: 0;
                z-index: -1;
                transition: opacity 0.4s ease;
                border-radius: 15px;
            }

            .kpi-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 15px 25px rgba(0, 0, 0, 0.5);
                border-color: rgba(41, 128, 185, 0.5);
                animation: float 6s ease-in-out infinite;
            }

            .kpi-card:hover::before {
                opacity: 1;
            }

            .kpi-card::after {
                content: '';
                position: absolute;
                width: 200%;
                height: 200%;
                top: -50%;
                left: -50%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
                transform: rotate(30deg);
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: none;
            }

            .kpi-card:hover::after {
                opacity: 1;
            }

            .particle {
                position: absolute;
                width: 4px;
                height: 4px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                pointer-events: none;
                opacity: 0;
            }

            .kpi-card:hover .particle {
                animation: particle 1.5s ease-out infinite;
            }

            .kpi-card:hover .particle:nth-child(1) { --tx: 20px; --ty: -20px; animation-delay: 0s; }
            .kpi-card:hover .particle:nth-child(2) { --tx: -20px; --ty: -15px; animation-delay: 0.2s; }
            .kpi-card:hover .particle:nth-child(3) { --tx: 15px; --ty: 20px; animation-delay: 0.4s; }
            .kpi-card:hover .particle:nth-child(4) { --tx: -15px; --ty: 15px; animation-delay: 0.6s; }

            .kpi-icon { 
                font-size: 2.8rem; 
                margin-bottom: 10px; 
                color: #ff8c42; 
                transition: transform 0.3s ease;
                position: relative;
            }

            .kpi-title { 
                font-size: 1.3rem; 
                color: #ecf0f1; 
                margin-bottom: 10px; 
                font-weight: 600; 
                transition: color 0.3s ease;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }

            .kpi-value { 
                font-size: 2.2rem; 
                font-weight: bold; 
                color: #ffffff; 
                margin-bottom: 5px; 
                transition: all 0.3s ease;
                position: relative;
            }

            .kpi-subtext { 
                font-size: 1rem; 
                color: #bdc3c7; 
                font-style: italic; 
                transition: color 0.3s ease;
                opacity: 0.8;
            }
            
            .kpi-card:hover .kpi-icon { 
                transform: scale(1.1); 
                color: #f39c12; 
            }

            .kpi-card:hover .kpi-title { 
                color: #3498db; 
            }

            .kpi-card:hover .kpi-value { 
                text-shadow: 0 0 15px rgba(52, 152, 219, 0.7);
                letter-spacing: 1px; 
            }

            .kpi-card:hover .kpi-subtext { 
                color: #e0e0e0; 
                opacity: 1;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    col7 = st.columns(1)[0]

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="kpi-icon">📊</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["total_safety_events"]}</div>
            <div class="kpi-value">{total_safety_events}</div>
            <div class="kpi-subtext">All recorded safety events</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="kpi-icon">⚠️</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["total_speeding_events"]}</div>
            <div class="kpi-value">{total_speeding_events}</div>
            <div class="kpi-subtext">Speeding incidents</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="kpi-icon">🔥</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["extreme_risk_events"]}</div>
            <div class="kpi-value">{extreme_risk_events}</div>
            <div class="kpi-subtext">High-risk incidents</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="kpi-icon">🚩</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["fleet_most_violations"]}</div>
            <div class="kpi-value">{top_group}</div>
            <div class="kpi-subtext">Total: {top_group_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="kpi-icon">🚛</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["avg_speed"]}</div>
            <div class="kpi-value">{average_speed}</div>
            <div class="kpi-subtext">Across all vehicles</div>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="kpi-icon">⚡</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["avg_overspeed"]}</div>
            <div class="kpi-value">{average_overspeed}</div>
            <div class="kpi-subtext">Above speed limit</div>
        </div>
        """, unsafe_allow_html=True)
    with col7:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="kpi-icon">👥</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["top_offenders"]}</div>
            <div class="kpi-value">{top_offenders}</div>
            <div class="kpi-subtext">By event count</div>
        </div>
        """, unsafe_allow_html=True)
    render_glow_line()

# -----------------------------------------------------------------------------
# CHART RENDERING FUNCTIONS (Event distribution, group comparison, top vehicles, time series, maps, dynamic table)
# -----------------------------------------------------------------------------
def render_event_distribution(filtered_df: pd.DataFrame, event_df=None):
    """Bar chart for event distribution by fleet group."""
    render_chart_title("event_distribution")
    if st.session_state.get("data_source") == "sql" and event_df is None:
        try:
            filter_conditions = []
            selections = st.session_state.get("selections", {})
            if selections:
                if selections.get("selected_license_plate") != "All":
                    filter_conditions.append(f"[License Plate] = '{selections['selected_license_plate']}'")
                if selections.get("selected_groups"):
                    groups_str = ", ".join([f"'{group}'" for group in selections.get("selected_groups", [])])
                    if groups_str:
                        filter_conditions.append(f"[Group] IN ({groups_str})")
                if selections.get("selected_dates"):
                    if isinstance(selections["selected_dates"], (list, tuple)) and len(selections["selected_dates"]) == 2:
                        start_date, end_date = selections["selected_dates"]
                        start_date_str = start_date.strftime('%Y-%m-%d')
                        end_date_str = end_date.strftime('%Y-%m-%d')
                        filter_conditions.append(f"[Shift Date] >= '{start_date_str}' AND [Shift Date] <= '{end_date_str}'")
                if selections.get("selected_shift") != "All":
                    filter_conditions.append(f"[Shift] = '{selections['selected_shift']}'")
                if selections.get("selected_events"):
                    events_str = ", ".join([f"'{event}'" for event in selections.get("selected_events", [])])
                    if events_str:
                        filter_conditions.append(f"[Event Type] IN ({events_str})")
            excluded_events = ["Occlusion", "PCW", "Tired", "Overspeed warning in the area", "Short Following Distance"]
            excluded_events_str = ", ".join([f"'{event}'" for event in excluded_events])
            where_clause = "WHERE " + " AND ".join(filter_conditions) if filter_conditions else ""
            if where_clause:
                where_clause += f" AND [Event Type] NOT IN ({excluded_events_str})"
            else:
                where_clause = f"WHERE [Event Type] NOT IN ({excluded_events_str})"
            sql_query = f"""
                SELECT [Group], COUNT(*) as [Event Count]
                FROM dbo.FMS_SPEED
                {where_clause}
                GROUP BY [Group]
                ORDER BY [Event Count] DESC
            """
            group_events = run_sql_query(sql_query)
            if not group_events.empty:
                fig_bar = px.bar(
                    group_events,
                    x="Group",
                    y="Event Count",
                    color="Event Count",
                    color_continuous_scale=[(0, "#2E8B57"), (1, "#F24C3D")],
                    labels={"Event Count": "Number of Events", "Group": "Fleet Group"},
                    text="Event Count"
                )
                fig_bar.update_layout(
                    xaxis_title="Fleet Group",
                    yaxis_title="Number of Events",
                    height=500,
                    margin=dict(l=50, r=50, t=40, b=50),
                    hovermode="x unified"
                )
                fig_bar.update_traces(
                    hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                render_glow_line()
                return
        except Exception as e:
            st.warning(f"Could not use direct SQL query for event distribution: {e}. Falling back to pandas.")
    if event_df is None:
        excluded_events = ["Occlusion", "PCW", "Tired", "Overspeed warning in the area", "Short Following Distance"]
        event_df = filtered_df[~filtered_df["Event Type"].isin(excluded_events)] if "Event Type" in filtered_df.columns else filtered_df.copy()
    if event_df.empty or "Group" not in event_df.columns:
        st.warning("⚠️ No data available for event distribution.")
        return
    group_events = event_df.groupby("Group").size().reset_index(name="Event Count")
    fig_bar = px.bar(
        group_events,
        x="Group",
        y="Event Count",
        color="Event Count",
        color_continuous_scale=[(0, "#2E8B57"), (1, "#F24C3D")],
        labels={"Event Count": "Number of Events", "Group": "Fleet Group"},
        text="Event Count"
    )
    fig_bar.update_layout(
        xaxis_title="Fleet Group",
        yaxis_title="Number of Events",
        height=500,
        margin=dict(l=50, r=50, t=40, b=50),
        hovermode="x unified"
    )
    fig_bar.update_traces(
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    render_glow_line()

def render_event_distribution_detailed(filtered_df: pd.DataFrame):
    """Detailed pie charts for event distribution by fleet group."""
    render_chart_title("event_distribution_detailed")
    excluded_events = ["Occlusion", "PCW", "FCW", "Tired", "Overspeed warning in the area", "Short Following Distance"]
    detail_df = filtered_df[~filtered_df["Event Type"].isin(excluded_events)] if "Event Type" in filtered_df.columns else filtered_df.copy()
    lang = st.session_state.language
    if lang == "ZH":
        if "Group" in detail_df.columns:
            detail_df["Group_Translated"] = detail_df["Group"].map(lambda x: group_translation.get(x, x))
        if "Event Type" in detail_df.columns:
            detail_df["Event Type_Translated"] = detail_df["Event Type"].map(lambda x: event_translation.get(x, x))
        group_col, event_col, group_label = "Group_Translated", "Event Type_Translated", "组别"
    else:
        group_col, event_col, group_label = "Group", "Event Type", "Group"
    groups = sorted(detail_df[group_col].unique()) if group_col in detail_df.columns else []
    view_mode = st.radio(
        TRANSLATIONS[lang]["view_mode_label"],
        options=[TRANSLATIONS[lang]["view_mode_all_groups"], TRANSLATIONS[lang]["view_mode_one_by_one"]],
        index=1,
        horizontal=True
    )
    safety_colors = ["#FF6B6B", "#4ECDC4", "#556270", "#C7F464", "#FFA500", "#6B5B95", "#F7CAC9"]
    if groups:
        if view_mode == TRANSLATIONS[lang]["view_mode_all_groups"]:
            cols = st.columns(2)
            for i, group in enumerate(groups):
                with cols[i % 2]:
                    st.subheader(f"{group_label}: {group}")
                    group_df = detail_df[detail_df[group_col] == group]
                    if not group_df.empty:
                        grouped = group_df.groupby(event_col).size().reset_index(name="Count")
                        fig_pie = px.pie(
                            grouped,
                            names=event_col,
                            values="Count",
                            hole=0.4,
                            color_discrete_sequence=safety_colors,
                            hover_data={"Count": True}
                        )
                        fig_pie.update_traces(
                            textinfo='percent+label',
                            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}",
                            marker=dict(line=dict(color='#ffffff', width=2)),
                            hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
                        )
                        fig_pie.update_layout(
                            margin=dict(l=20, r=20, t=60, b=20),
                            legend=dict(title="Event Types", orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5),
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.warning(f"No data available for {group}.")
        else:
            tabs = st.tabs([f"{group_label}: {g}" for g in groups])
            for i, group in enumerate(groups):
                with tabs[i]:
                    group_df = detail_df[detail_df[group_col] == group]
                    if not group_df.empty:
                        grouped = group_df.groupby(event_col).size().reset_index(name="Count")
                        fig_pie = px.pie(
                            grouped,
                            names=event_col,
                            values="Count",
                            hole=0.3,
                            color_discrete_sequence=safety_colors,
                            hover_data={"Count": True}
                        )
                        fig_pie.update_traces(
                            textinfo='percent+label',
                            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}",
                            marker=dict(line=dict(color='#ffffff', width=2)),
                            hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
                        )
                        fig_pie.update_layout(
                            margin=dict(l=20, r=20, t=60, b=20),
                            legend=dict(title="Event Types", orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5),
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.warning(f"No data available for {group}.")
    else:
        st.warning("No fleet groups available after filtering.")
    render_glow_line()

def render_group_comparison(filtered_df: pd.DataFrame, grouped_data=None):
    """Dual-axis chart comparing speeding event percentages and counts by fleet group."""
    render_chart_title("group_comparison")
    if st.session_state.get("data_source") == "sql" and grouped_data is None:
        try:
            filter_conditions = []
            selections = st.session_state.get("selections", {})
            if selections:
                if selections.get("selected_license_plate") != "All":
                    filter_conditions.append(f"[License Plate] = '{selections['selected_license_plate']}'")
                if selections.get("selected_groups"):
                    groups_str = ", ".join([f"'{group}'" for group in selections.get("selected_groups", [])])
                    if groups_str:
                        filter_conditions.append(f"[Group] IN ({groups_str})")
                if selections.get("selected_dates"):
                    if isinstance(selections["selected_dates"], (list, tuple)) and len(selections["selected_dates"]) == 2:
                        start_date, end_date = selections["selected_dates"]
                        start_date_str = start_date.strftime('%Y-%m-%d')
                        end_date_str = end_date.strftime('%Y-%m-%d')
                        filter_conditions.append(f"[Shift Date] >= '{start_date_str}' AND [Shift Date] <= '{end_date_str}'")
                if selections.get("selected_shift") != "All":
                    filter_conditions.append(f"[Shift] = '{selections['selected_shift']}'")
                filter_conditions.append(f"[Event Type] = 'Speeding'")
            else:
                filter_conditions = [f"[Event Type] = 'Speeding'"]
            where_clause = "WHERE " + " AND ".join(filter_conditions)
            total_query = f"SELECT COUNT(*) as total_count FROM dbo.FMS_SPEED {where_clause}"
            total_df = run_sql_query(total_query)
            total_events = total_df.iloc[0]['total_count'] if not total_df.empty else 1
            sql_query = f"""
                SELECT [Group], COUNT(*) as [Number of Events]
                FROM dbo.FMS_SPEED
                {where_clause}
                GROUP BY [Group]
                ORDER BY [Number of Events] DESC
            """
            grouped_data = run_sql_query(sql_query)
            if not grouped_data.empty:
                grouped_data['Percentage'] = (grouped_data['Number of Events'] / total_events) * 100
                theme_colors = {"chart-1": "#2E8B57", "chart-2": "#FF7F0F"}
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(
                    go.Bar(
                        x=grouped_data['Group'],
                        y=grouped_data['Percentage'],
                        name="Percentage of Speeding Events",
                        text=[f"{p:.1f}%" for p in grouped_data['Percentage']],
                        textposition='outside',
                        customdata=grouped_data['Number of Events'],
                        marker=dict(color=theme_colors["chart-1"], opacity=0.9, line=dict(width=1, color="black")),
                        hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
                    ),
                    secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(
                        x=grouped_data['Group'],
                        y=grouped_data['Number of Events'],
                        name="Number of Speeding Events",
                        mode='lines+markers',
                        line=dict(color=theme_colors["chart-2"], width=3),
                        marker=dict(size=8, color=theme_colors["chart-2"], line=dict(width=2, color='white')),
                        hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
                    ),
                    secondary_y=True
                )
                for i, (group, count) in enumerate(zip(grouped_data["Group"], grouped_data["Number of Events"])):
                    fig.add_annotation(
                        x=group,
                        y=0,
                        text=f"{count}",
                        showarrow=False,
                        font=dict(size=14, color="black"),
                        yshift=-15
                    )
                fig.update_layout(
                    xaxis_title="Fleet Group",
                    yaxis_title="Percentage of Speeding Events",
                    yaxis2=dict(title="Number of Speeding Events", overlaying='y', side='right', showgrid=False),
                    height=450,
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                    margin=dict(l=50, r=50, t=40, b=50),
                    xaxis=dict(showgrid=False, linecolor='black', linewidth=2),
                    yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)', zeroline=False)
                )
                st.plotly_chart(fig, use_container_width=True)
                render_glow_line()
                return
        except Exception as e:
            st.warning(f"Could not use direct SQL query for group comparison: {e}. Falling back to pandas.")
    if grouped_data is None:
        speeding_df = filtered_df[filtered_df['Event Type'] == 'Speeding']
        grouped_data = speeding_df.groupby('Group').size().reset_index(name='Number of Events')
        total_events = grouped_data['Number of Events'].sum() if not grouped_data.empty else 1
        grouped_data['Percentage'] = (grouped_data['Number of Events'] / total_events) * 100
    if grouped_data.empty:
        st.warning("⚠️ No data available for group comparison.")
        return
    theme_colors = {"chart-1": "#2E8B57", "chart-2": "#FF7F0F"}
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=grouped_data['Group'],
            y=grouped_data['Percentage'],
            name="Percentage of Speeding Events",
            text=[f"{p:.1f}%" for p in grouped_data['Percentage']],
            textposition='outside',
            customdata=grouped_data['Number of Events'],
            marker=dict(color=theme_colors["chart-1"], opacity=0.9, line=dict(width=1, color="black")),
            hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=grouped_data['Group'],
            y=grouped_data['Number of Events'],
            name="Number of Speeding Events",
            mode='lines+markers',
            line=dict(color=theme_colors["chart-2"], width=3),
            marker=dict(size=8, color=theme_colors["chart-2"], line=dict(width=2, color='white')),
            hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=13, font_family="Helvetica", font_color="black")
        ),
        secondary_y=True
    )
    for i, (group, count) in enumerate(zip(grouped_data["Group"], grouped_data["Number of Events"])):
        fig.add_annotation(
            x=group,
            y=0,
            text=f"{count}",
            showarrow=False,
            font=dict(size=14, color="black"),
            yshift=-15
        )
    fig.update_layout(
        xaxis_title="Fleet Group",
        yaxis_title="Percentage of Speeding Events",
        yaxis2=dict(title="Number of Speeding Events", overlaying='y', side='right', showgrid=False),
        height=450,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=40, b=50),
        xaxis=dict(showgrid=False, linecolor='black', linewidth=2),
        yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)', zeroline=False)
    )
    st.plotly_chart(fig, use_container_width=True)
    render_glow_line()

def render_top_speeding_vehicles_chart(filtered_df: pd.DataFrame):
    """Bar chart showing the Top 20 Vehicles with Most Speeding Events."""
    render_chart_title("top_speeding_vehicles")
    try:
        if 'Event Type' in filtered_df.columns and 'License Plate' in filtered_df.columns:
            speeding_df = filtered_df[filtered_df['Event Type'] == 'Speeding'].copy()
            if not speeding_df.empty:
                license_counts = speeding_df.groupby(['License Plate', 'Group']).agg(
                    event_count=('License Plate', 'count'),
                    avg_speed=('Overspeeding Value', 'mean'),
                    max_speed=('Overspeeding Value', 'max'),
                    unique_days=('Shift Date', lambda x: len(pd.to_datetime(x).dt.date.unique()))
                ).reset_index()
                license_counts['Vehicle Info'] = license_counts['License Plate'] + ' (' + license_counts['Group'] + ')'
                top_vehicles = license_counts.sort_values('event_count', ascending=False).head(15)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=top_vehicles['Vehicle Info'],
                    y=top_vehicles['event_count'],
                    marker=dict(
                        color=top_vehicles['avg_speed'],
                        colorscale='RdYlGn_r',
                        colorbar=dict(title="Avg Speed (km/h)")
                    ),
                    text=top_vehicles['event_count'],
                    textposition='auto',
                    hovertemplate="<b>%{x}</b><br>" +
                                  "Events: %{y}<br>" +
                                  "Avg Speed: %{customdata[0]:.1f} km/h<br>" +
                                  "Max Speed: %{customdata[1]} km/h<br>" +
                                  "Active Days: %{customdata[2]}<extra></extra>",
                    customdata=top_vehicles[['avg_speed', 'max_speed', 'unique_days']].values
                ))
                fig.update_layout(
                    title=dict(
                        text=get_translation("top_speeding_vehicles", st.session_state.language),
                        font=dict(size=24, family="Arial", color="#2a3f5f")
                    ),
                    xaxis=dict(
                        title="",
                        tickfont=dict(size=12),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Number of Speeding Events",
                            font=dict(size=14)
                        ),
                        tickfont=dict(size=12)
                    ),
                    template="plotly_white",
                    height=600,
                    margin=dict(t=80, b=100, l=80, r=40),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode='closest'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No speeding events found in the selected data.")
        else:
            st.warning("Required columns for speeding chart not found in the data.")
    except Exception as e:
        st.error(f"Error generating speeding vehicles chart: {e}")
    render_glow_line()

def render_time_series(filtered_df: pd.DataFrame, avg_speeding=None):
    """Time series chart for average speeding values with a trend line."""
    render_chart_title("time_series")
    if st.session_state.get("data_source") == "sql" and avg_speeding is None:
        try:
            filter_conditions = []
            selections = st.session_state.get("selections", {})
            if selections:
                if selections.get("selected_license_plate") != "All":
                    filter_conditions.append(f"[License Plate] = '{selections['selected_license_plate']}'")
                if selections.get("selected_groups"):
                    groups_str = ", ".join([f"'{group}'" for group in selections.get("selected_groups", [])])
                    if groups_str:
                        filter_conditions.append(f"[Group] IN ({groups_str})")
                if selections.get("selected_dates"):
                    if isinstance(selections["selected_dates"], (list, tuple)) and len(selections["selected_dates"]) == 2:
                        start_date, end_date = selections["selected_dates"]
                        start_date_str = start_date.strftime('%Y-%m-%d')
                        end_date_str = end_date.strftime('%Y-%m-%d')
                        filter_conditions.append(f"[Shift Date] >= '{start_date_str}' AND [Shift Date] <= '{end_date_str}'")
                if selections.get("selected_shift") != "All":
                    filter_conditions.append(f"[Shift] = '{selections['selected_shift']}'")
                if selections.get("selected_events"):
                    events_str = ", ".join([f"'{event}'" for event in selections.get("selected_events", [])])
                    if events_str:
                        filter_conditions.append(f"[Event Type] IN ({events_str})")
            where_clause = "WHERE " + " AND ".join(filter_conditions) if filter_conditions else ""
            sql_query = f"""
                SELECT [Shift Date], AVG([Overspeeding Value]) as [Overspeeding Value]
                FROM dbo.FMS_SPEED
                {where_clause}
                GROUP BY [Shift Date]
                ORDER BY [Shift Date]
            """
            avg_speeding = run_sql_query(sql_query)
            if not avg_speeding.empty and len(avg_speeding) >= 2:
                x_numeric = np.arange(len(avg_speeding))
                y_values = pd.to_numeric(avg_speeding['Overspeeding Value'], errors='coerce')
                valid_indices = ~np.isnan(y_values)
                if sum(valid_indices) < 2:
                    st.warning("⚠️ Not enough valid numeric data points to compute a trend line.")
                    return
                x_valid = x_numeric[valid_indices]
                y_valid = y_values[valid_indices]
                trend_coeffs = np.polyfit(x_valid, y_valid, 1)
                trend_line = np.polyval(trend_coeffs, x_numeric)
                avg_speeding['Trend'] = trend_line
                fig_ts = go.Figure()
                fig_ts.add_trace(
                    go.Scatter(
                        x=avg_speeding['Shift Date'],
                        y=avg_speeding['Trend'],
                        mode='lines',
                        name="Trend Line",
                        line=dict(width=2, color='#ff7f0e', dash='dot'),
                        hovertemplate="<b>Date: %{x}</b><br>Trend: %{y:.2f} Km/h"
                    )
                )
                fig_ts.add_trace(
                    go.Scatter(
                        x=avg_speeding['Shift Date'],
                        y=avg_speeding['Overspeeding Value'],
                        mode='lines+markers',
                        name="Average Speeding Value",
                        line=dict(width=3, color='#1f77b4'),
                        marker=dict(
                            size=8,
                            color=avg_speeding['Overspeeding Value'],
                            colorscale='YlOrRd',
                            showscale=False,
                            line=dict(width=1, color='black')
                        ),
                        hovertemplate="<b>Date: %{x}</b><br>Average Speeding Value: %{y:.2f} Km/h"
                    )
                )
                final_trend_value = avg_speeding['Trend'].iloc[-1]
                fig_ts.add_annotation(
                    x=avg_speeding['Shift Date'].iloc[-1],
                    y=avg_speeding['Trend'].iloc[-1],
                    ax=avg_speeding['Shift Date'].iloc[-2],
                    ay=avg_speeding['Trend'].iloc[-2],
                    xref="x", yref="y", axref="x", ayref="y",
                    showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor='#ff7f0e'
                )
                fig_ts.add_annotation(
                    x=avg_speeding['Shift Date'].iloc[-1],
                    y=avg_speeding['Trend'].iloc[-1],
                    text=f" {final_trend_value:.2f} Km/h",
                    showarrow=False,
                    font=dict(size=14, color='#ff7f0e', family='Arial Black'),
                    xshift=50,
                    yshift=0,
                    align='left'
                )
                fig_ts.update_layout(
                    title="Average Over-Speeding Values Over Time",
                    xaxis_title="Date",
                    yaxis_title="Average Speeding Value (Km/h)",
                    height=400,
                    margin=dict(l=50, r=100, t=40, b=50)
                )
                st.plotly_chart(fig_ts, use_container_width=True)
                render_glow_line()
                return
            else:
                st.warning("⚠️ Not enough data points from SQL to compute a trend line.")
        except Exception as e:
            st.warning(f"Could not use direct SQL query for time series: {e}. Falling back to pandas.")
    if avg_speeding is None:
        if "Overspeeding Value" in filtered_df.columns:
            avg_speeding = filtered_df.groupby('Shift Date')['Overspeeding Value'].mean().reset_index()
        else:
            avg_speeding = pd.DataFrame()
    if avg_speeding.empty:
        st.warning("Overspeeding Value data not available.")
        return
    if len(avg_speeding) >= 2:
        try:
            x_numeric = np.arange(len(avg_speeding))
            y_values = pd.to_numeric(avg_speeding['Overspeeding Value'], errors='coerce')
            valid_indices = ~np.isnan(y_values)
            if sum(valid_indices) < 2:
                st.warning("⚠️ Not enough valid numeric data points to compute a trend line.")
                return
            x_valid = x_numeric[valid_indices]
            y_valid = y_values[valid_indices]
            trend_coeffs = np.polyfit(x_valid, y_valid, 1)
            trend_line = np.polyval(trend_coeffs, x_numeric)
            avg_speeding['Trend'] = trend_line
            fig_ts = go.Figure()
            fig_ts.add_trace(
                go.Scatter(
                    x=avg_speeding['Shift Date'],
                    y=avg_speeding['Trend'],
                    mode='lines',
                    name="Trend Line",
                    line=dict(width=2, color='#ff7f0e', dash='dot'),
                    hovertemplate="<b>Date: %{x}</b><br>Trend: %{y:.2f} Km/h"
                )
            )
            fig_ts.add_trace(
                go.Scatter(
                    x=avg_speeding['Shift Date'],
                    y=avg_speeding['Overspeeding Value'],
                    mode='lines+markers',
                    name="Average Speeding Value",
                    line=dict(width=3, color='#1f77b4'),
                    marker=dict(
                        size=8,
                        color=avg_speeding['Overspeeding Value'],
                        colorscale='YlOrRd',
                        showscale=False,
                        line=dict(width=1, color='black')
                    ),
                    hovertemplate="<b>Date: %{x}</b><br>Average Speeding Value: %{y:.2f} Km/h"
                )
            )
            final_trend_value = avg_speeding['Trend'].iloc[-1]
            fig_ts.add_annotation(
                x=avg_speeding['Shift Date'].iloc[-1],
                y=avg_speeding['Trend'].iloc[-1],
                ax=avg_speeding['Shift Date'].iloc[-2],
                ay=avg_speeding['Trend'].iloc[-2],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor='#ff7f0e'
            )
            fig_ts.add_annotation(
                x=avg_speeding['Shift Date'].iloc[-1],
                y=avg_speeding['Trend'].iloc[-1],
                text=f" {final_trend_value:.2f} Km/h",
                showarrow=False,
                font=dict(size=14, color='#ff7f0e', family='Arial Black'),
                xshift=50,
                yshift=0,
                align='left'
            )
            fig_ts.update_layout(
                title="Average Over-Speeding Values Over Time",
                xaxis_title="Date",
                yaxis_title="Average Speeding Value (Km/h)",
                height=400,
                margin=dict(l=50, r=100, t=40, b=50)
            )
            st.plotly_chart(fig_ts, use_container_width=True)
        except Exception as e:
            st.warning(f"Unable to compute trend line: {e}")
    else:
        st.warning("⚠️ Not enough data points to compute a trend line.")
    render_glow_line()

def render_geospatial_maps(filtered_df: pd.DataFrame, map_df=None):
    """Render geospatial visualizations for speeding events."""
    render_chart_title("scatter_plot_header")
    roads_geojson_path = os.path.join("assets", "WBN_roads.geojson")
    roads_geojson = None
    if os.path.exists(roads_geojson_path):
        try:
            with open(roads_geojson_path, 'r') as f:
                roads_geojson = json.load(f)
        except Exception as e:
            st.error(f"Error loading WBN roads GeoJSON: {e}")
    lat_col = 'Start Lat' if 'Start Lat' in filtered_df.columns else ('latitude' if 'latitude' in filtered_df.columns else None)
    lon_col = 'Start Lng' if 'Start Lng' in filtered_df.columns else ('longitude' if 'longitude' in filtered_df.columns else None)
    if lat_col is None or lon_col is None:
        st.error("No valid latitude/longitude columns found in the data.")
        return
    if map_df is None:
        if "Risk Level" not in filtered_df.columns:
            st.warning("⚠️ 'Risk Level' column missing! Defaulting to all speeding events.")
            filtered_df = assign_risk_level(filtered_df)
        map_df = filtered_df[(filtered_df['Event Type'] == 'Speeding') & 
                    (filtered_df['Risk Level'].isin(['Extreme', 'High', 'Medium']))]
        map_df = map_df.dropna(subset=[lat_col, lon_col])
    if map_df.empty:
        st.warning("⚠️ No speeding event data available for visualization.")
    else:
        color_map = {'Extreme': '#FF0000', 'High': '#FFA500', 'Medium': '#FFFF00'}
        hover_data = []
        for _, row in map_df.iterrows():
            hover_text = f"<b>Risk Level:</b> {row.get('Risk Level', 'N/A')}<br>"
            if 'License Plate' in row:
                hover_text += f"<b>License Plate:</b> {row['License Plate']}<br>"
            if 'Driver' in row:
                hover_text += f"<b>Driver:</b> {row['Driver']}<br>"
            if 'Max Speed(Km/h)' in row:
                hover_text += f"<b>Max Speed:</b> {row['Max Speed(Km/h)']} Km/h<br>"
            if 'Overspeeding Value' in row:
                hover_text += f"<b>Overspeeding Value:</b> {row['Overspeeding Value']} Km/h<br>"
            hover_data.append(hover_text)
        map_df['hover_text'] = hover_data
        fig = px.scatter_map(
            map_df,
            lat=lat_col,
            lon=lon_col,
            color='Risk Level',
            color_discrete_map=color_map,
            size=[12]*len(map_df),
            size_max=15,
            zoom=10,
            height=700,
            hover_name='Risk Level',
            hover_data={ 'hover_text': True, lat_col: False, lon_col: False, 'Risk Level': False },
            title='Speeding Events by Location'
        )
        fig.update_layout(
            mapbox_style=st.selectbox(
                "Select Map Style",
                options=["open-street-map", "carto-darkmatter"],
                index=0,
                key="mapbox_style_selector"
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255, 255, 255, 0.8)"),
            mapbox=dict(
                center=dict(
                    lat=map_df[lat_col].mean(),
                    lon=map_df[lon_col].mean()
                ),
                zoom=10
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    render_chart_title("heatmap")
    if not filtered_df.empty and all(col in filtered_df.columns for col in ['Start Lat', 'Start Lng']):
        map_df_heat = filtered_df[filtered_df['Event Type'] == 'Speeding'].dropna(subset=['Start Lat', 'Start Lng'])
        if map_df_heat.empty:
            lat_center, lon_center = 37.7749, -122.4194
        else:
            lat_center = map_df_heat['Start Lat'].mean()
            lon_center = map_df_heat['Start Lng'].mean()
        m_heat = leafmap.Map(center=(lat_center, lon_center), zoom=12)
        m_heat.add_basemap("SATELLITE")
        if roads_geojson:
            try:
                m_heat.add_geojson(roads_geojson_path, layer_name="WBN Roads", style={"color": "#3388ff", "weight": 3})
                st.info("✅ WBN roads layer added to the heatmap.")
            except Exception as e:
                st.error(f"Error loading WBN roads GeoJSON for heatmap: {e}")
        map_df_heat = map_df_heat.dropna(subset=['Start Lat', 'Start Lng', 'Overspeeding Value'])
        try:
            m_heat.add_heatmap(
                map_df_heat,
                latitude='Start Lat',
                longitude='Start Lng',
                value='Overspeeding Value',
                radius=20,
                name="Speeding Heatmap",
                key='map_visualization'
            )
        except Exception as e:
            st.error(f"Error creating heatmap: {e}")
            st.info("This may be due to NaN values in the data. Please ensure your data has valid coordinates and values.")
        uploaded_files_2 = st.file_uploader(
            "Upload additional geospatial files for heatmap", 
            type=["zip", "geojson", "shp", "dbf", "shx", "prj", "cpg", "gpkg"], 
            key="geo_upload_2", 
            accept_multiple_files=True
        )
        if uploaded_files_2:
            try:
                if any(f.name.endswith(".shp") for f in uploaded_files_2):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for f in uploaded_files_2:
                            with open(os.path.join(tmpdir, f.name), "wb") as tmp_file:
                                tmp_file.write(f.getbuffer())
                        shp_file = [f for f in os.listdir(tmpdir) if f.endswith(".shp")][0]
                        shp_path = os.path.join(tmpdir, shp_file)
                        gdf_layer = gpd.read_file(shp_path)
                        m_heat.add_gdf(gdf_layer, layer_name="Uploaded Layer")
                elif any(f.name.endswith((".geojson", ".gpkg", ".json")) for f in uploaded_files_2):
                    gdf_layer = gpd.read_file(uploaded_files_2[0])
                    m_heat.add_gdf(gdf_layer, layer_name="Uploaded Layer")
            except Exception as e:
                st.error(f"Error processing uploaded files: {e}")
        m_heat.to_streamlit(height=600, key='map_visualization')
    else:
        st.warning("⚠️ No valid geospatial data available for heatmap.")
    render_glow_line()

def render_dynamic_table(df: pd.DataFrame):
    """Dynamic table viewer with selectable columns."""
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    render_chart_title("dynamic_table")
    default_columns = [
        "License Plate", 
        "Group", 
        "Event Type", 
        "Area", 
        "Speed Limit", 
        "Max Speed(Km/h)", 
        "Overspeeding Value", 
        "Driver", 
        "Shift Date", 
        "Shift", 
        "Risk Level"
    ]
    available_columns = df.columns.tolist()
    default_columns = [col for col in default_columns if col in available_columns]
    col_select, col_anim = st.columns([3, 2])
    with col_select:
        st.markdown("### 📋 Select Columns to Display")
        selected_columns = st.multiselect(
            "Choose columns to display", 
            available_columns, 
            default=default_columns
        )
    with col_anim:
        lottie_anim = load_lottie_json("assets/ani9.json")
        if lottie_anim:
            st_lottie(lottie_anim, speed=1, width=400, height=400)
    if selected_columns:
        if st.session_state.language == "ZH":
            display_df = df.copy()
            for col in display_df.columns:
                translated_col = get_translation(col, st.session_state.language)
                if translated_col != col:
                    display_df = display_df.rename(columns={col: translated_col})
            st.dataframe(display_df[selected_columns], use_container_width=True)
        else:
            st.dataframe(df[selected_columns], use_container_width=True)
    else:
        st.warning("⚠️ Please select at least one column to display data.")
    render_glow_line()

def render_data_reports_section(df):
    """Render the data and reports section with download options."""
    st.header("📊 Data and Reports")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Download Raw Data")
        if st.button("Download CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Click to Download",
                data=csv,
                file_name="safety_data.csv",
                mime="text/csv"
            )
    with col2:
        st.subheader("Generate Report")
        if st.button("📊 Generate Report"):
            with st.spinner("Generating PDF report..."):
                report_path = generate_dashboard_report(df)
                if report_path:
                    with open(report_path, "rb") as pdf_file:
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_file,
                            file_name="safety_report.pdf",
                            mime="application/pdf"
                        )
                    st.success("Report generated successfully!")
                else:
                    st.error("Failed to generate report.")

# -----------------------------------------------------------------------------
# NAVIGATION FUNCTIONS
# -----------------------------------------------------------------------------
def render_navigation():
    """Render the navigation system for the dashboard."""
    lang = st.session_state.language
    st.markdown(
        """
        <style>
        .nav-pills {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .stButton > button {
            font-weight: 600 !important;
            padding: 12px 20px !important;
            border-radius: 8px !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        }
        .active-nav-button > button {
            background-color: #ff8c42 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    with st.container():
        st.markdown('<div class="nav-pills">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        nav_options = {
            "analytics": {"icon": "📊", "label": TRANSLATIONS[lang].get('analytics_nav', 'Analytics'), "column": col1},
            "maps": {"icon": "🗺️", "label": TRANSLATIONS[lang].get('maps_nav', 'Maps'), "column": col2},
            "data": {"icon": "📋", "label": TRANSLATIONS[lang].get('data_nav', 'Data & Reports'), "column": col3}
        }
        for section_id, section_info in nav_options.items():
            with section_info["column"]:
                if st.session_state.current_section == section_id:
                    st.markdown(f'<div class="active-nav-button">', unsafe_allow_html=True)
                    button_clicked = st.button(
                        f"{section_info['icon']} {section_info['label']}", 
                        key=f"nav_{section_id}",
                        use_container_width=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    button_clicked = st.button(
                        f"{section_info['icon']} {section_info['label']}", 
                        key=f"nav_{section_id}",
                        use_container_width=True
                    )
                if button_clicked:
                    st.session_state.current_section = section_id
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    render_glow_line()

@st.cache_data(ttl=3600)
def process_analytics_data(filtered_df: pd.DataFrame):
    """Process data for analytics charts (cached for performance)."""
    excluded_events = ["Occlusion", "PCW", "FCW", "Tired", "Overspeed warning in the area", "Short Following Distance"]
    event_df = filtered_df[~filtered_df["Event Type"].isin(excluded_events)] if "Event Type" in filtered_df.columns else filtered_df.copy()
    speeding_df = filtered_df[filtered_df['Event Type'] == 'Speeding']
    grouped_data = speeding_df.groupby('Group').size().reset_index(name='Number of Events')
    if not grouped_data.empty:
        total_events = grouped_data['Number of Events'].sum()
        grouped_data['Percentage'] = (grouped_data['Number of Events'] / total_events) * 100
    if 'Event Type' in filtered_df.columns and 'License Plate' in filtered_df.columns:
        speeding_vehicles = filtered_df[filtered_df['Event Type'] == 'Speeding']["License Plate"].value_counts().reset_index()
        speeding_vehicles.columns = ["License Plate", "Speeding Events"]
        speeding_vehicles = speeding_vehicles.head(20)
    else:
        speeding_vehicles = pd.DataFrame()
    if "Overspeeding Value" in filtered_df.columns:
        avg_speeding = filtered_df.groupby('Shift Date')['Overspeeding Value'].mean().reset_index()
    else:
        avg_speeding = pd.DataFrame()
    return {
        "event_df": event_df,
        "grouped_data": grouped_data,
        "speeding_vehicles": speeding_vehicles,
        "avg_speeding": avg_speeding
    }

@st.cache_data(ttl=3600)
def process_map_data(filtered_df: pd.DataFrame):
    """Process data for maps (cached for performance)."""
    if "Risk Level" not in filtered_df.columns:
        filtered_df = assign_risk_level(filtered_df)
    map_df = filtered_df[(filtered_df['Event Type'] == 'Speeding') & 
                 (filtered_df['Risk Level'].isin(['Extreme', 'High', 'Medium']))]
    map_df = map_df.dropna(subset=['Start Lat', 'Start Lng'])
    map_df_heat = filtered_df[filtered_df['Event Type'] == 'Speeding'].dropna(subset=['Start Lat', 'Start Lng'])
    return {
        "scatter_map_df": map_df,
        "heatmap_df": map_df_heat
    }

def render_dashboard(filtered_df: pd.DataFrame, analytics_data, map_data):
    """Render the main dashboard UI components."""
    render_glow_line()
    if 'data_source' in st.session_state:
        data_source = st.session_state.data_source
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            if data_source == "sql":
                st.success("✅ Connected to SQL Database")
            elif data_source == "upload":
                st.info("ℹ️ Using uploaded dataset")
            elif data_source == "network":
                st.info("ℹ️ Using network dataset")
            elif data_source == "sample":
                st.warning("⚠️ Using sample dataset - For demonstration purposes only")
        with col2:
            refresh_clicked = st.button("Refresh Data")
            refresh_needed = st.session_state.get('data_needs_refresh', False)
            
            if refresh_clicked:
                # Clear cached data on explicit refresh click
                st.session_state.pop('df', None)
                st.session_state.pop('data_needs_refresh', None)
                if st.session_state.get('pending_upload', False):
                    st.session_state.pop('pending_upload', None)
                st.rerun()
            elif refresh_needed:
                # Clear the flag but don't trigger refresh if we're already here because of a refresh
                # This prevents infinite refresh loops
                st.session_state.pop('data_needs_refresh', None)
                if not st.session_state.get('_refreshing', False):
                    st.session_state['_refreshing'] = True
                    st.rerun()
                else:
                    st.session_state.pop('_refreshing', None)
                
        with col3:
            if st.button("Database Settings"):
                st.switch_page("pages/4_⚙️_Settings.py")
    if 'sql_connection_error' in st.session_state and st.session_state.data_source != "sql":
        with st.expander("Database Connection Issues"):
            st.error(f"{st.session_state.sql_connection_error}")
            st.info("Use the 'Database Settings' button to configure your SQL Server connection.")
    render_kpis(filtered_df)
    render_navigation()
    current_section = st.session_state.current_section
    if current_section == "analytics":
        with st.spinner("Loading analytics..."):
            render_event_distribution(filtered_df, analytics_data["event_df"])
            render_event_distribution_detailed(filtered_df)
            render_group_comparison(filtered_df, analytics_data["grouped_data"])
            render_top_speeding_vehicles_chart(filtered_df)
            render_time_series(filtered_df, analytics_data["avg_speeding"])
    elif current_section == "maps":
        with st.spinner("Loading maps..."):
            scatter_map_df = map_data.get("scatter_map_df", None)
            render_geospatial_maps(filtered_df, scatter_map_df)
    elif current_section == "data":
        with st.spinner("Loading data and reports..."):
            render_dynamic_table(filtered_df)
            render_data_reports_section(filtered_df)

def main():
    """Main function to render the dashboard."""
    # Initialize language if not set
    if "language" not in st.session_state:
        st.session_state.language = "EN"
        
    render_header()
    render_file_upload()
    if "df" not in st.session_state:
        loading_container = st.empty()
        success_container = st.empty()
        error_container = st.empty()
        with loading_container:
            st.markdown("""
            <style>
            .loading-pulse {
                width: 64px;
                height: 64px;
                border: 5px solid #1D5B79;
                border-radius: 50%;
                position: relative;
                animation: pulse 1.5s cubic-bezier(0.24, 0, 0.38, 1) infinite;
            }
            .loading-pulse:before {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: #2E8B57;
                opacity: 0.6;
                animation: pulse-inner 1.5s cubic-bezier(0.24, 0, 0.38, 1) infinite;
            }
            @keyframes pulse {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(29, 91, 121, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(29, 91, 121, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(29, 91, 121, 0); }
            }
            @keyframes pulse-inner {
                0% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
                70% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.2; }
                100% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
            }
            </style>
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05)); border-radius: 15px; margin: 1rem 0; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);">
                <div class="loading-pulse"></div>
                <h2 style="color: #1D5B79; margin-top: 1rem; font-size: 24px; font-weight: 600; text-align: center;">Loading Data from SQL Database...</h2>
                <p style="color: #666; margin-top: 0.5rem; font-size: 16px; text-align: center;">Please wait while we fetch the latest safety records</p>
            </div>
            """, unsafe_allow_html=True)
        df = get_shared_data()
        if df.empty:
            loading_container.warning("⚠️ SQL Database connection failed. Checking alternative data sources...")
            st.session_state.sql_connection_error = "Failed to connect to SQL database. Please check your connection settings."
            if "uploaded_file" in st.session_state and st.session_state.uploaded_file is not None:
                with loading_container:
                    st.markdown("""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05)); border-radius: 15px; margin: 1rem 0; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);">
                        <div class="loading-pulse"></div>
                        <h2 style="color: #1D5B79; margin-top: 1rem; font-size: 24px; font-weight: 600; text-align: center;">Loading Uploaded Excel File...</h2>
                        <p style="color: #666; margin-top: 0.5rem; font-size: 16px; text-align: center;">Please wait while we process your uploaded data</p>
                    </div>
                    """, unsafe_allow_html=True)
                try:
                    df = pd.read_excel(st.session_state.uploaded_file)
                    if "Shift Date" in df.columns:
                        df["Shift Date"] = pd.to_datetime(df["Shift Date"], errors="coerce")
                        df.dropna(subset=["Shift Date"], inplace=True)
                        df["Date"] = df["Shift Date"].dt.date
                        if "Shift" in df.columns:
                            df["Shift"] = df["Shift"].str.capitalize()
                    st.session_state.data_source = "upload"
                    loading_container.empty()
                    with success_container:
                        st.success("✅ Successfully loaded data from uploaded Excel file!")
                        time.sleep(2)
                    success_container.empty()
                except Exception as e:
                    loading_container.error(f"⚠️ Failed to read uploaded file: {str(e)}")
                    st.session_state.data_source = "none"
                    df = pd.DataFrame()
            else:
                DEFAULT_FILE_PATH = r"\\10.211.3.254\04. Mining\WBN - FLEET MANAGEMENT SYSTEM\Haulage DT Safety Event Report\FMS Event Data Query.xlsx"
                if os.path.exists(DEFAULT_FILE_PATH):
                    try:
                        df = pd.read_excel(DEFAULT_FILE_PATH)
                        if "Shift Date" in df.columns:
                            df["Shift Date"] = pd.to_datetime(df["Shift Date"], errors="coerce")
                            df.dropna(subset=["Shift Date"], inplace=True)
                            df["Date"] = df["Shift Date"].dt.date
                            if "Shift" in df.columns:
                                df["Shift"] = df["Shift"].str.capitalize()
                        st.session_state.data_source = "network"
                        loading_container.empty()
                        with success_container:
                            st.success("✅ Successfully loaded data from network file!")
                            time.sleep(2)
                        success_container.empty()
                    except Exception as e:
                        loading_container.error(f"⚠️ Failed to read network file: {str(e)}")
                        st.session_state.data_source = "none"
                        df = pd.DataFrame()
                else:
                    try:
                        sample_data_path = os.path.join("assets", "sample_data.xlsx")
                        if os.path.exists(sample_data_path):
                            df = pd.read_excel(sample_data_path)
                            if "Shift Date" in df.columns:
                                df["Shift Date"] = pd.to_datetime(df["Shift Date"], errors="coerce")
                                df.dropna(subset=["Shift Date"], inplace=True)
                                df["Date"] = df["Shift Date"].dt.date
                                if "Shift" in df.columns:
                                    df["Shift"] = df["Shift"].str.capitalize()
                            st.session_state.data_source = "sample"
                            loading_container.empty()
                            with success_container:
                                st.warning("⚠️ Using sample dataset - For demonstration purposes only")
                                time.sleep(2)
                            success_container.empty()
                        else:
                            loading_container.error("⚠️ No data available. Please upload an Excel file.")
                            st.session_state.data_source = "none"
                            df = pd.DataFrame()
                    except Exception as e:
                        loading_container.error(f"⚠️ Failed to load any data: {str(e)}")
                        st.session_state.data_source = "none"
                        df = pd.DataFrame()
        else:
            loading_container.empty()
            with success_container:
                st.success("✅ Data loaded successfully from SQL!")
                time.sleep(1)
            success_container.empty()
            st.session_state.data_source = "sql"
        if not df.empty:
            st.session_state.df = df
        else:
            loading_container.error("⚠️ No data available. Please upload an Excel file or check database connection.")
            st.warning("To use your own data, please upload an Excel file above.")
            st.stop()
    else:
        df = st.session_state.df
    if not df.empty and 'Overspeeding Value' in df.columns:
        df = assign_risk_level(df)
        selections = render_sidebar(df)
        st.session_state.selections = selections
        filtered_df = filter_data(df, selections)
    render_dashboard(filtered_df, process_analytics_data(filtered_df), process_map_data(filtered_df))

if __name__ == "__main__":
    main()
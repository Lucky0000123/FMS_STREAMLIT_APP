# Standard library imports
import streamlit as st
import time
import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import tempfile
from io import BytesIO
import uuid

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="FMS Safety Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

import json
import os
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

# Third-party library imports
import geopandas as gpd
import leafmap.foliumap as leafmap
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from streamlit_lottie import st_lottie
import pyodbc

# Mapping libraries
import folium
from folium.plugins import MarkerCluster, HeatMap

# Local imports
from utils import (
    process_dataframe,
    assign_risk_level,
    load_lottie_json,
    render_chart_title,
    render_header,
    filter_data,
    render_glow_line,
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

# Apply global CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Initialize session state variables
if "using_default_data" not in st.session_state:
    st.session_state.using_default_data = True
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "language" not in st.session_state:
    st.session_state.language = "EN"
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "rerun_triggered" not in st.session_state:
    st.session_state.rerun_triggered = False

# Navigation state
if "current_section" not in st.session_state:
    st.session_state.current_section = "analytics"

# Add session state for preloaded map data
if "map_data_loaded" not in st.session_state:
    st.session_state.map_data_loaded = False
if "preloaded_map_df" not in st.session_state:
    st.session_state.preloaded_map_df = None
if "preloaded_map_df_heat" not in st.session_state:
    st.session_state.preloaded_map_df_heat = None

# -----------------------------------------------------------------------------
# TRANSLATION DICTIONARIES
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# THEME CONFIGURATION
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
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
    Assign a 'Risk Level' based on 'Overspeeding Value'.
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
            st.info("ℹ️ Using default dataset.")
        else:
            st.error("⚠️ Default data file not found!")
            return pd.DataFrame()

    if "Shift Date" in df.columns:
        df["Shift Date"] = pd.to_datetime(df["Shift Date"], errors="coerce")
        df.dropna(subset=["Shift Date"], inplace=True)
        df["Date"] = df["Shift Date"].dt.date
        df["Shift"] = df["Shift"].str.capitalize()
    return df

def read_uploaded_geospatial_file(uploaded_file) -> gpd.GeoDataFrame:
    """
    Save an uploaded geospatial file to a temporary file and return a GeoDataFrame.
    """
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

# -----------------------------------------------------------------------------
# SIDEBAR RENDERING
# -----------------------------------------------------------------------------
def render_sidebar(df: pd.DataFrame) -> dict:
    """Render sidebar filters and return user selections."""
    ASSETS_DIR = Path(__file__).parent / "assets"
    
    with st.sidebar:
        # Display logo
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            st.markdown("""
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 1rem;
                margin-bottom: 1.5rem;
                background: linear-gradient(180deg, rgba(29, 91, 121, 0.05) 0%, rgba(46, 139, 87, 0.05) 100%);
                border-radius: 15px;
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
            ">
            """, unsafe_allow_html=True)
            st.image(str(logo_path), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Add custom CSS for the sidebar
        st.markdown("""
            <style>
            /* Base Section Title Styling */
            .section-title {
                padding: 12px 20px;
                border-radius: 12px;
                font-size: 1.1rem;
                font-weight: 600;
                margin: 15px 0 10px 0;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                color: white;
            }

            /* All Section Titles - Using Theme Colors */
            .section-title.theme,
            .section-title.language,
            .section-title.date,
            .section-title.shift,
            .section-title.vehicle,
            .section-title.fleet,
            .section-title.event {
                background: linear-gradient(135deg, #1D5B79, #2E8B57);
                box-shadow: 0 4px 15px rgba(29, 91, 121, 0.15);
            }

            .section-title.theme:hover,
            .section-title.language:hover,
            .section-title.date:hover,
            .section-title.shift:hover,
            .section-title.vehicle:hover,
            .section-title.fleet:hover,
            .section-title.event:hover {
                background: linear-gradient(135deg, #2E8B57, #1D5B79);
                transform: translateY(-2px);
            }

            /* Selection Indicator Styling */
            .selection-indicator {
                background: rgba(29, 91, 121, 0.1);
                border-left: 4px solid #1D5B79;
                padding: 10px 15px;
                margin: 5px 0;
                border-radius: 0 8px 8px 0;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                color: #1D5B79;
            }

            .selection-indicator:hover {
                background: rgba(29, 91, 121, 0.15);
                transform: translateX(5px);
            }

            /* Section Title Content */
            .section-title span {
                position: relative;
                z-index: 1;
                display: flex;
                align-items: center;
                gap: 8px;
                width: 100%;
                justify-content: space-between;
            }

            .section-title span::after {
                content: '›';
                font-size: 1.5rem;
                opacity: 0.8;
                transition: transform 0.3s ease;
            }

            .section-title:hover span::after {
                transform: translateX(5px);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Theme Selection
        st.markdown('<div class="section-title theme"><span>🎨 Theme Selection</span></div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🌞 Light", key="light_theme", use_container_width=True):
                    st.session_state.theme = "light"
                    switch_theme()
            with col2:
                if st.button("🌙 Dark", key="dark_theme", use_container_width=True):
                    st.session_state.theme = "dark"
                    switch_theme()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="selection-indicator theme-indicator">Current Theme: {st.session_state.theme.capitalize()}</div>', unsafe_allow_html=True)

        # Language Selection
        st.markdown('<div class="section-title language"><span>🌍 Language Settings</span></div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🇬🇧 English", key="english_lang", use_container_width=True):
                    st.session_state.language = "EN"
                    st.rerun()
            with col2:
                if st.button("🇨🇳 中文", key="chinese_lang", use_container_width=True):
                    st.session_state.language = "ZH"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="selection-indicator language-indicator">Current Language: {"English" if st.session_state.language == "EN" else "中文"}</div>', unsafe_allow_html=True)

        # Get min and max dates from the DataFrame
        if not df.empty and "Date" in df.columns:
            min_date = df["Date"].min()
            max_date = df["Date"].max()
        else:
            min_date = max_date = None

        # Date Range Selection
        st.markdown('<div class="section-title date"><span>📅 Date Range Filter</span></div>', unsafe_allow_html=True)
        
        # Quick filter buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📅 Last Week", key="last_week", use_container_width=True):
                if min_date and max_date:
                    today = max_date
                    last_week_start = max(min_date, (today - pd.Timedelta(days=7)))
                    last_week_end = today
                    st.session_state.date_range = (last_week_start, last_week_end)
        with col2:
            if st.button("📅 This Month", key="this_month", use_container_width=True):
                if min_date and max_date:
                    today = max_date
                    month_start = max(min_date, today.replace(day=1))
                    month_end = today
                    st.session_state.date_range = (month_start, month_end)
        
        # Date range selection
        if 'date_range' in st.session_state:
            selected_dates = st.date_input(
                "Pick a Date Range",
                st.session_state.date_range,
                min_value=min_date,
                max_value=max_date
            )
        else:
            selected_dates = st.date_input(
                "Pick a Date Range",
                (min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        
        # Show selected date range
        if selected_dates:
            start_date, end_date = selected_dates
            st.markdown(f'<div class="selection-indicator date-indicator">Selected Dates: {start_date} to {end_date}</div>', unsafe_allow_html=True)

        # Shift Selection
        st.markdown('<div class="section-title shift"><span>⏰ Shift Filter</span></div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🌅 All", key="shift_all", use_container_width=True):
                    st.session_state.selected_shift = "All"
            with col2:
                if st.button("☀️ Day", key="shift_day", use_container_width=True):
                    st.session_state.selected_shift = "Siang"
            with col3:
                if st.button("🌙 Night", key="shift_night", use_container_width=True):
                    st.session_state.selected_shift = "Malam"
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show selected shift
            selected_shift = st.session_state.get("selected_shift", "All")
            st.markdown(f'<div class="selection-indicator shift-indicator">Selected Shift: {selected_shift}</div>', unsafe_allow_html=True)

        # License Plate Selection
        st.markdown('<div class="section-title vehicle"><span>🚛 Vehicle Selection</span></div>', unsafe_allow_html=True)
        selected_plate = st.selectbox("Select License Plate", ["All"] + sorted(df["License Plate"].unique()), label_visibility="collapsed")

        # Fleet Group Selection
        st.markdown('<div class="section-title fleet"><span>🚜 Fleet Groups</span></div>', unsafe_allow_html=True)
        selected_groups = st.multiselect("Select Fleet Group", sorted(df["Group"].unique()), default=list(df["Group"].unique()), label_visibility="collapsed")

        # Event Types Selection
        st.markdown('<div class="section-title event"><span>⚠️ Event Categories</span></div>', unsafe_allow_html=True)
        default_events = ["Smoking", "Speeding", "Closed Eyes", "Phone", "Yawn"]
        all_events = sorted(df["Event Type"].unique())
        default_events = [event for event in default_events if event in all_events]
        other_events = [event for event in all_events if event not in default_events]
        all_events = default_events + other_events
        selected_events = st.multiselect(
            "Select Event Types",
            options=all_events,
            default=default_events,
            label_visibility="collapsed"
        )
    
    # Set default shift to "All" if no selection is made
    if 'selected_shift' not in locals():
        selected_shift = "All"
    
    return {
        "selected_shift": selected_shift,
        "selected_dates": selected_dates,
        "selected_license_plate": selected_plate,
        "selected_groups": selected_groups,
        "selected_events": selected_events
    }

def filter_data(df: pd.DataFrame, selections: dict) -> pd.DataFrame:
    """Apply sidebar filters to the dataset."""
    filtered_df = df.copy()
    if selections["selected_license_plate"] != "All":
        filtered_df = filtered_df[filtered_df["License Plate"] == selections["selected_license_plate"]]
    if selections["selected_groups"]:
        filtered_df = filtered_df[filtered_df["Group"].isin(selections["selected_groups"])]
    if selections["selected_dates"]:
        if isinstance(selections["selected_dates"], (list, tuple)) and len(selections["selected_dates"]) == 2:
            start_date, end_date = selections["selected_dates"]
            # Convert dates to pandas datetime for comparison
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            # Convert the Date column to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(filtered_df["Date"]):
                filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])
            filtered_df = filtered_df[(filtered_df["Date"] >= start_date) & (filtered_df["Date"] <= end_date)]
    if selections["selected_shift"] != "All":
        filtered_df = filtered_df[filtered_df["Shift"] == selections["selected_shift"]]
    if selections["selected_events"]:
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

# -----------------------------------------------------------------------------
# HEADER RENDERING
# -----------------------------------------------------------------------------
def render_header():
    """Render header with title, logo, animation, and file upload."""
    lang = st.session_state.language
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
    uploaded_file = st.file_uploader(
        "Drag and drop file here", 
        type=["xlsx"], 
        help="Limit 200MB per file • XLSX", 
        key="file_upload_key"
    )
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.using_default_data = False
        st.success("✅ File uploaded successfully! Using your dataset.")
    else:
        st.session_state.using_default_data = True

# -----------------------------------------------------------------------------
# KPI RENDERING
# -----------------------------------------------------------------------------
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
        top_offenders_series = filtered_df['Driver'].value_counts().head(5)
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
            .kpi-card {
                background: linear-gradient(145deg, #1c2b3a, #23374d);
                border-radius: 15px;
                padding: 20px;
                margin: 10px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .kpi-card:hover {
                transform: scale(1.05);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            }
            .kpi-icon { font-size: 2.8rem; margin-bottom: 10px; color: #ff8c42; }
            .kpi-title { font-size: 1.3rem; color: #ecf0f1; margin-bottom: 10px; font-weight: 600; }
            .kpi-value { font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
            .kpi-subtext { font-size: 1rem; color: #bdc3c7; font-style: italic; }
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
            <div class="kpi-icon">📊</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["total_safety_events"]}</div>
            <div class="kpi-value">{total_safety_events}</div>
            <div class="kpi-subtext">All recorded safety events</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">⚠️</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["total_speeding_events"]}</div>
            <div class="kpi-value">{total_speeding_events}</div>
            <div class="kpi-subtext">Speeding incidents</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🔥</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["extreme_risk_events"]}</div>
            <div class="kpi-value">{extreme_risk_events}</div>
            <div class="kpi-subtext">High-risk incidents</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🚩</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["fleet_most_violations"]}</div>
            <div class="kpi-value">{top_group}</div>
            <div class="kpi-subtext">Total: {top_group_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["avg_speed"]}</div>
            <div class="kpi-value">{average_speed}</div>
            <div class="kpi-subtext">Across all vehicles</div>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">⚡</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["avg_overspeed"]}</div>
            <div class="kpi-value">{average_overspeed}</div>
            <div class="kpi-subtext">Above speed limit</div>
        </div>
        """, unsafe_allow_html=True)
    with col7:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div class="kpi-title">{TRANSLATIONS[lang]["top_offenders"]}</div>
            <div class="kpi-value">{top_offenders}</div>
            <div class="kpi-subtext">By event count</div>
        </div>
        """, unsafe_allow_html=True)
    render_glow_line()

# -----------------------------------------------------------------------------
# CHART RENDERING FUNCTIONS
# -----------------------------------------------------------------------------
def render_event_distribution(filtered_df: pd.DataFrame, event_df=None):
    """Bar chart for total event distribution by fleet group."""
    render_chart_title("event_distribution")
    
    # Use pre-processed data if available, otherwise process it here
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
    
    # Use pre-processed data if available, otherwise process it here
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
    
    if 'Event Type' in filtered_df.columns and 'License Plate' in filtered_df.columns:
        speeding_df = filtered_df[filtered_df['Event Type'] == 'Speeding']
        speeding_vehicles = speeding_df["License Plate"].value_counts().reset_index()
        speeding_vehicles.columns = ["License Plate", "Speeding Events"]
        speeding_vehicles = speeding_vehicles.head(20)
    else:
        speeding_vehicles = pd.DataFrame()
    
    if speeding_vehicles.empty:
        st.warning("⚠️ No speeding events found for the selected filters.")
        return
    
    fig = px.bar(
        speeding_vehicles,
        x="License Plate",
        y="Speeding Events",
        color="Speeding Events",
        color_continuous_scale=[(0, "#2E8B57"), (1, "#F24C3D")],
        text="Speeding Events"
    )
    fig.update_layout(
        xaxis_title="Vehicle",
        yaxis_title="Speeding Events",
        height=500,
        margin=dict(l=50, r=50, t=40, b=50)
    )
    st.plotly_chart(fig, use_container_width=True)
    render_glow_line()

def render_time_series(filtered_df: pd.DataFrame, avg_speeding=None):
    """Time series chart for average speeding values with a trend line."""
    render_chart_title("time_series")
    
    # Use pre-processed data if available, otherwise process it here
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
            # Ensure data is numeric before trend calculation
            x_numeric = np.arange(len(avg_speeding))
            y_values = pd.to_numeric(avg_speeding['Overspeeding Value'], errors='coerce')
            
            # Skip NaN values in the trend calculation
            valid_indices = ~np.isnan(y_values)
            if sum(valid_indices) < 2:
                st.warning("⚠️ Not enough valid numeric data points to compute a trend line.")
                return
                
            x_valid = x_numeric[valid_indices]
            y_valid = y_values[valid_indices]
            
            # Calculate trend line with valid numeric data only
            trend_coeffs = np.polyfit(x_valid, y_valid, 1)
            trend_line = np.polyval(trend_coeffs, x_numeric)
            avg_speeding['Trend'] = trend_line
            fig_ts = go.Figure()
            
            # Add trend line first (so it appears behind)
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
            
            # Add average speeding value line second (so it appears in front)
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
            
            # Add trend line arrow and value annotation
            final_trend_value = avg_speeding['Trend'].iloc[-1]
            fig_ts.add_annotation(
                x=avg_speeding['Shift Date'].iloc[-1],
                y=avg_speeding['Trend'].iloc[-1],
                ax=avg_speeding['Shift Date'].iloc[-2],
                ay=avg_speeding['Trend'].iloc[-2],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor='#ff7f0e'
            )
            
            # Add trend value text annotation with arrow style
            fig_ts.add_annotation(
                x=avg_speeding['Shift Date'].iloc[-1],
                y=avg_speeding['Trend'].iloc[-1],
                text=f" {final_trend_value:.2f} Km/h",
                showarrow=False,
                font=dict(size=14, color='#ff7f0e', family='Arial Black'),
                xshift=50,  # Shift text to the right
                yshift=0,   # Keep at same y-level
                align='left'
            )
            
            fig_ts.update_layout(
                title="Average Over-Speeding Values Over Time",
                xaxis_title="Date",
                yaxis_title="Average Speeding Value (Km/h)",
                height=400,
                margin=dict(l=50, r=100, t=40, b=50)  # Increased right margin to accommodate annotation
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
    
    # Define the path to the WBN roads GeoJSON file
    roads_geojson_path = os.path.join("assets", "WBN_roads.geojson")
    
    # Load the GeoJSON file if it exists
    roads_geojson = None
    if os.path.exists(roads_geojson_path):
        try:
            with open(roads_geojson_path, 'r') as f:
                roads_geojson = json.load(f)
        except Exception as e:
            st.error(f"Error loading WBN roads GeoJSON: {e}")
    
    # Always determine valid latitude/longitude columns from the filtered dataframe
    lat_col = 'Start Lat' if 'Start Lat' in filtered_df.columns else ('latitude' if 'latitude' in filtered_df.columns else None)
    lon_col = 'Start Lng' if 'Start Lng' in filtered_df.columns else ('longitude' if 'longitude' in filtered_df.columns else None)
    if lat_col is None or lon_col is None:
        st.error("No valid latitude/longitude columns found in the data.")
        return

    # If no pre-processed map_df is provided, create one using the determined latitude/longitude columns
    if map_df is None:
        if "Risk Level" not in filtered_df.columns:
            st.warning("⚠️ 'Risk Level' column missing! Defaulting to all speeding events.")
            filtered_df = assign_risk_level(filtered_df)
        map_df = filtered_df[(filtered_df['Event Type'] == 'Speeding') & 
                    (filtered_df['Risk Level'].isin(['Extreme', 'High', 'Medium']))]
        map_df = map_df.dropna(subset=[lat_col, lon_col])
    
    # Check if data is available for visualization
    if map_df.empty:
        st.warning("⚠️ No speeding event data available for visualization.")
    else:
        # Define colors for risk levels
        color_map = {'Extreme': '#FF0000', 'High': '#FFA500', 'Medium': '#FFFF00'}
        
        # Create hover text with additional information
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
        
        # Create the scatter mapbox plot using the dynamic column names.
        # Here we pass a constant marker size array so that the points are always visible.
        fig = px.scatter_map(
            map_df,
            lat=lat_col,
            lon=lon_col,
            color='Risk Level',
            color_discrete_map=color_map,
            size=[12]*len(map_df),  # constant marker size for clarity
            size_max=15,
            zoom=10,
            height=700,
            hover_name='Risk Level',
            hover_data={
                'hover_text': True,
                lat_col: False,
                lon_col: False,
                'Risk Level': False
            },
            title='Speeding Events by Location'
        )
        
        # Set a clean map layout
        fig.update_layout(
            mapbox_style=st.selectbox(
                "Select Map Style",
                options=["open-street-map", "carto-darkmatter",],
                index=0,
                key="mapbox_style_selector"
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)"
            ),
            mapbox=dict(
                center=dict(
                    lat=map_df[lat_col].mean(),
                    lon=map_df[lon_col].mean()
                ),
                zoom=10
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Add a separator between the two maps
    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    
    # Render the heatmap section
    render_chart_title("heatmap")
    if not filtered_df.empty and all(col in filtered_df.columns for col in ['Start Lat', 'Start Lng']):
        map_df_heat = filtered_df[filtered_df['Event Type'] == 'Speeding'].dropna(subset=['Start Lat', 'Start Lng'])
        if map_df_heat.empty:
            lat_center, lon_center = 37.7749, -122.4194  # Default center (San Francisco)
        else:
            lat_center = map_df_heat['Start Lat'].mean()
            lon_center = map_df_heat['Start Lng'].mean()
        
        # Create the heatmap
        m_heat = leafmap.Map(center=(lat_center, lon_center), zoom=12)
        m_heat.add_basemap("SATELLITE")
        
        # Add WBN roads as a permanent layer if the file exists
        if roads_geojson:
            try:
                m_heat.add_geojson(roads_geojson_path, layer_name="WBN Roads", style={"color": "#3388ff", "weight": 3})
                st.info("✅ WBN roads layer added to the heatmap.")
            except Exception as e:
                st.error(f"Error loading WBN roads GeoJSON for heatmap: {e}")
        
        m_heat.add_heatmap(
            map_df_heat,
            latitude='Start Lat',
            longitude='Start Lng',
            value='Overspeeding Value',
            radius=20,
            name="Speeding Heatmap",
            key='map_visualization'
        )
        
        # Add file uploader for heatmap
        uploaded_files_2 = st.file_uploader(
            "Upload additional geospatial files for heatmap", 
            type=["zip", "geojson", "shp", "dbf", "shx", "prj", "cpg", "gpkg"], 
            key="geo_upload_2", 
            accept_multiple_files=True
        )
        
        # Process uploaded files for heatmap
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
        
        # Display the heatmap
        m_heat.to_streamlit(height=600, key='map_visualization')
    else:
        st.warning("⚠️ No valid geospatial data available for heatmap.")
    
    # Add a glow line separator
    render_glow_line()


def render_dynamic_table(df: pd.DataFrame):
    """Dynamic table viewer with selectable columns."""
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    render_chart_title("dynamic_table")
    
    # Set default columns to display
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
    
    # Filter available columns and ensure defaults exist in the dataframe
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
        # Check if we need to translate column names
        if st.session_state.language == "ZH":
            # Translate column names for display
            display_df = df.copy()
            for col in display_df.columns:
                translated_col = get_translation(col, st.session_state.language)
                if translated_col != col:  # Only rename if there's a translation
                    display_df = display_df.rename(columns={col: translated_col})
            
            # Display the translated DataFrame
            st.dataframe(display_df[selected_columns], use_container_width=True)
        else:
            # Display the original DataFrame
            st.dataframe(df[selected_columns], use_container_width=True)
    else:
        st.warning("⚠️ Please select at least one column to display data.")
    render_glow_line()

# -----------------------------------------------------------------------------
# REPORT GENERATION FUNCTIONS
# -----------------------------------------------------------------------------
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
                        btn = st.download_button(
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
    
    # Add custom CSS for the navigation buttons
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
    
    # Create a container for the navigation buttons
    with st.container():
        st.markdown('<div class="nav-pills">', unsafe_allow_html=True)
        
        # Create columns for the navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        # Define the navigation options
        nav_options = {
            "analytics": {"icon": "📊", "label": TRANSLATIONS[lang].get('analytics_nav', 'Analytics'), "column": col1},
            "maps": {"icon": "🗺️", "label": TRANSLATIONS[lang].get('maps_nav', 'Maps'), "column": col2},
            "data": {"icon": "📋", "label": TRANSLATIONS[lang].get('data_nav', 'Data & Reports'), "column": col3}
        }
        
        # Create the navigation buttons
        for section_id, section_info in nav_options.items():
            with section_info["column"]:
                # Add a div with active class if this is the current section
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

# -----------------------------------------------------------------------------
# DASHBOARD RENDERING
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def process_analytics_data(filtered_df: pd.DataFrame):
    """Process data for analytics charts (cached for performance)."""
    # Prepare data for event distribution
    excluded_events = ["Occlusion", "PCW", "Tired", "Overspeed warning in the area", "Short Following Distance"]
    event_df = filtered_df[~filtered_df["Event Type"].isin(excluded_events)] if "Event Type" in filtered_df.columns else filtered_df.copy()
    
    # Prepare data for group comparison
    speeding_df = filtered_df[filtered_df['Event Type'] == 'Speeding']
    grouped_data = speeding_df.groupby('Group').size().reset_index(name='Number of Events')
    if not grouped_data.empty:
        total_events = grouped_data['Number of Events'].sum()
        grouped_data['Percentage'] = (grouped_data['Number of Events'] / total_events) * 100
    
    # Prepare data for top speeding vehicles
    if 'Event Type' in filtered_df.columns and 'License Plate' in filtered_df.columns:
        speeding_vehicles = filtered_df[filtered_df['Event Type'] == 'Speeding']["License Plate"].value_counts().reset_index()
        speeding_vehicles.columns = ["License Plate", "Speeding Events"]
        speeding_vehicles = speeding_vehicles.head(20)
    else:
        speeding_vehicles = pd.DataFrame()
    
    # Prepare data for time series
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def process_map_data(filtered_df: pd.DataFrame):
    """Process data for maps (cached for performance)."""
    # Ensure Risk Level is assigned
    if "Risk Level" not in filtered_df.columns:
        filtered_df = assign_risk_level(filtered_df)
    
    # Filter data for speeding events with valid coordinates for scatter plot
    map_df = filtered_df[(filtered_df['Event Type'] == 'Speeding') & 
                 (filtered_df['Risk Level'].isin(['Extreme', 'High', 'Medium']))]
    map_df = map_df.dropna(subset=['Start Lat', 'Start Lng'])
    
    # Filter data for speeding events with valid coordinates for heatmap
    map_df_heat = filtered_df[filtered_df['Event Type'] == 'Speeding'].dropna(subset=['Start Lat', 'Start Lng'])
    
    return {
        "scatter_map_df": map_df,
        "heatmap_df": map_df_heat
    }

def render_dashboard(filtered_df: pd.DataFrame, analytics_data, map_data):
    """Render the main dashboard UI components."""
    # Page Header
    from utils import render_header as render_header_with_params
    render_header_with_params(
        "FMS Safety Dashboard",
        "",
        "assets/dashboard.png"
    )
    render_glow_line()
    
    # Database connection status
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
            if st.button("Refresh Data"):
                st.experimental_rerun()
        
        with col3:
            if st.button("Database Settings"):
                st.switch_page("pages/4_⚙️_Settings.py")

    if 'sql_connection_error' in st.session_state and st.session_state.data_source != "sql":
        with st.expander("Database Connection Issues"):
            st.error(f"{st.session_state.sql_connection_error}")
            st.info("Use the 'Database Settings' button to configure your SQL Server connection.")

    # Continue with existing code
    # KPI Metrics
    render_kpis(filtered_df)
    
    # Render navigation
    render_navigation()
    
    # Render the selected section
    current_section = st.session_state.current_section
    
    if current_section == "analytics":
        # Analytics section
        with st.spinner("Loading analytics..."):
            # Render analytics charts
            render_event_distribution(filtered_df, analytics_data["event_df"])
            render_event_distribution_detailed(filtered_df)
            render_group_comparison(filtered_df, analytics_data["grouped_data"])
            render_top_speeding_vehicles_chart(filtered_df)
            render_time_series(filtered_df, analytics_data["avg_speeding"])
    
    elif current_section == "maps":
        # Maps section
        with st.spinner("Loading maps..."):
            # Use preloaded map data if available
            scatter_map_df = map_data.get("scatter_map_df", None)
            render_geospatial_maps(filtered_df, scatter_map_df)
    
    elif current_section == "data":
        # Data and Reports section
        with st.spinner("Loading data and reports..."):
            render_dynamic_table(filtered_df)
            render_data_reports_section(filtered_df)

# -----------------------------------------------------------------------------
# MAIN FUNCTION
# -----------------------------------------------------------------------------
def main():
    """Main function to render the dashboard."""
    render_header()
    render_file_upload()

    # Check if data needs to be loaded
    if "df" not in st.session_state:
        # Create containers for loading states
        loading_container = st.empty()
        success_container = st.empty()
        
        # Show loading animation
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
                0% {
                    transform: scale(0.95);
                    box-shadow: 0 0 0 0 rgba(29, 91, 121, 0.7);
                }
                70% {
                    transform: scale(1);
                    box-shadow: 0 0 0 15px rgba(29, 91, 121, 0);
                }
                100% {
                    transform: scale(0.95);
                    box-shadow: 0 0 0 0 rgba(29, 91, 121, 0);
                }
            }
            
            @keyframes pulse-inner {
                0% {
                    transform: translate(-50%, -50%) scale(1);
                    opacity: 0.6;
                }
                70% {
                    transform: translate(-50%, -50%) scale(1.2);
                    opacity: 0.2;
                }
                100% {
                    transform: translate(-50%, -50%) scale(1);
                    opacity: 0.6;
                }
            }
            </style>
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
                border-radius: 15px;
                margin: 1rem 0;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            ">
                <div class="loading-pulse"></div>
                <h2 style="
                    color: #1D5B79;
                    margin-top: 1rem;
                    font-size: 24px;
                    font-weight: 600;
                    text-align: center;
                ">Loading Data from SQL Database...</h2>
                <p style="
                    color: #666;
                    margin-top: 0.5rem;
                    font-size: 16px;
                    text-align: center;
                ">Please wait while we fetch the latest safety records</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Load data
        df = get_shared_data()
        
        if df.empty:
            loading_container.error("⚠️ No data available. Please check the data source.")
            st.stop()
        else:
            # Show success message briefly
            loading_container.empty()
            with success_container:
                st.success("✅ Data loaded successfully!")
                time.sleep(1)  # Show success message for 1 second
            success_container.empty()
            
            # Store data in session state
            st.session_state.df = df
    else:
        # Data already loaded, just use it from session state
        df = st.session_state.df
    
    # Process the data if needed
    if not df.empty and 'Overspeeding Value' in df.columns:
        df = assign_risk_level(df)

        # Apply filters
        selections = render_sidebar(df)
        st.session_state.selections = selections  # Store selections in session state
        filtered_df = filter_data(df, selections)

    # Render the dashboard
    render_dashboard(filtered_df, process_analytics_data(filtered_df), process_map_data(filtered_df))

if __name__ == "__main__":
    main()

"""
Driver Performance & Warning Letters Page
(Rewritten with preserved page title (with Lottie animation and translate button)
and KPI CSS animations. Fixed boolean ambiguity when filtering data.)
"""

import os
import sys
import json
import time
import uuid
import tempfile
import datetime
from datetime import timedelta, date
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
from docx2pdf import convert as docx2pdf_convert
from mailmerge import MailMerge
import pythoncom
import PyPDF2  # Import PyPDF2 for merging PDFs

# Custom utility imports – adjust paths as necessary
from utils import (
    render_glow_line,
    load_data,
    switch_theme,
    render_chart_title,
    get_shared_data,
    filter_data,
    clear_shared_data,
    render_header
)
from sidebar import render_sidebar
from translations import get_translation, get_event_translation
from config import (
    THEME_CONFIG,
    RISK_THRESHOLDS,
    UPLOAD_CONFIG,
    PDF_CONFIG,
    DB_CONFIG,
    GLOBAL_CSS
)
from pdf_generator import generate_report, generate_dashboard_report

# =============================================================================
# PAGE CONFIGURATION & THEME SETUP
# =============================================================================
st.set_page_config(
    page_title="Driver Performance & Warning Letters",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# LANGUAGE TOGGLE & LOTTIE ANIMATION (Page Title Section)
# ------------------------------------------------------------------------------
if "language" not in st.session_state:
    st.session_state["language"] = "EN"

# Initialize theme in session state
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

def toggle_language():
    st.session_state["language"] = "ZH" if st.session_state["language"] == "EN" else "EN"

col_trans, col_anim = st.columns([1, 1])
with col_trans:
    st.markdown(f"""
    <div style="padding: 20px; border-radius: 12px; margin-top: 20px; text-align: center;
                background: linear-gradient(to right, rgba(29, 91, 121, 0.05), transparent);">
        <h3 style="color: #1D5B79; margin-bottom: 15px; font-size: 32px; font-weight: 600; letter-spacing: 0.5px;">
            {get_translation("click_for_translation", st.session_state.language)}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    translation_label = "切换中文" if st.session_state["language"] == "EN" else "Switch to English"
    st.button(translation_label, on_click=toggle_language)
with col_anim:
    try:
        with open("assets/ani6.json", "r") as f:
            animation_data = json.load(f)
        st_lottie(animation_data, speed=1, reverse=False, loop=True, quality="high", height=150)
    except Exception as e:
        st.warning("Animation could not be loaded. Please ensure the JSON file exists in the assets folder.")
st.markdown("<br>", unsafe_allow_html=True)
render_glow_line()

# ------------------------------------------------------------------------------
# GLOBAL CSS & CUSTOM STYLING (Including KPI CSS Animations)
# ------------------------------------------------------------------------------
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Define header_color based on theme
header_color = "#1D5B79" if st.session_state.theme == "light" else "#3A95FF"

# Additional CSS overrides for KPI cards, sidebar, buttons, etc.
st.markdown(f"""
<style>
/* KPI Cards with CSS animations */
.kpi-card {{
    background: linear-gradient(145deg, {"rgba(30,30,30,1)" if st.session_state.theme=="dark" else "#ffffff"}, {"rgba(45,45,45,1)" if st.session_state.theme=="dark" else "#f5f7fa"});
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(29, 91, 121, 0.1);
    transition: all 0.5s ease;
    color: {"white" if st.session_state.theme=="dark" else "#2E3440"};
    margin-bottom: 15px;
    position: relative;
    overflow: hidden;
    perspective: 1000px;
    transform-style: preserve-3d;
}}
.kpi-card:hover {{
    transform: translateY(-8px) scale(1.02) rotateX(5deg);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15), 0 0 15px {"rgba(58, 149, 255, 0.5)" if st.session_state.theme=="dark" else "rgba(29, 91, 121, 0.3)"};
    border-color: {"rgba(58, 149, 255, 0.4)" if st.session_state.theme=="dark" else "rgba(29, 91, 121, 0.3)"};
}}
.kpi-card:hover::after {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 16px;
    background: transparent;
    border: 2px solid transparent;
    box-shadow: 0 0 15px {"rgba(58, 149, 255, 0.7)" if st.session_state.theme=="dark" else "rgba(29, 91, 121, 0.5)"};
    opacity: 0.8;
    pointer-events: none;
}}
@keyframes textBounce {{
    0% {{ transform: scale(1); }}
    50% {{ transform: scale(1.1); }}
    100% {{ transform: scale(1.05); }}
}}
.kpi-card.blue {{
    border-left: 4px solid #1D5B79;
}}
.kpi-card.blue:hover {{
    background: linear-gradient(145deg, {"rgba(35,35,40,1)" if st.session_state.theme=="dark" else "#ffffff"}, {"rgba(50,55,65,1)" if st.session_state.theme=="dark" else "#f0f5fa"});
    border-left: 4px solid #3A95FF;
}}
.kpi-card.green {{
    border-left: 4px solid #2E8B57;
}}
.kpi-card.green:hover {{
    background: linear-gradient(145deg, {"rgba(35,40,35,1)" if st.session_state.theme=="dark" else "#ffffff"}, {"rgba(50,65,55,1)" if st.session_state.theme=="dark" else "#f0faf5"});
    border-left: 4px solid #66C2A5;
}}
.kpi-card.red {{
    border-left: 4px solid #FF5C5C;
}}
.kpi-card.red:hover {{
    background: linear-gradient(145deg, {"rgba(40,35,35,1)" if st.session_state.theme=="dark" else "#ffffff"}, {"rgba(65,50,50,1)" if st.session_state.theme=="dark" else "#faf0f0"});
    border-left: 4px solid #FF8A80;
}}
.kpi-title {{
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
    color: {"lightblue" if st.session_state.theme=="dark" else "#1D5B79"};
    letter-spacing: 0.5px;
    position: relative;
    display: inline-block;
}}
.kpi-title::after {{
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 40%;
    height: 2px;
    background: linear-gradient(90deg, {"#3A95FF" if st.session_state.theme=="dark" else "#1D5B79"}, transparent);
}}
.kpi-value {{
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1.2;
    background: linear-gradient(45deg, {"#3A95FF" if st.session_state.theme=="dark" else "#1D5B79"}, {"#64B5F6" if st.session_state.theme=="dark" else "#468B97"});
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.kpi-card.blue .kpi-value {{
    background: linear-gradient(45deg, #1D5B79, #4DA9FF);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.kpi-card.green .kpi-value {{
    background: linear-gradient(45deg, #2E8B57, #66C2A5);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.kpi-card.red .kpi-value {{
    background: linear-gradient(45deg, #E65758, #FF8A80);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.kpi-card:hover .kpi-value {{
    animation: textBounce 0.5s ease-in-out;
}}
/* Sidebar (Simplified) Styling */
section[data-testid="stSidebar"] {{
    background: {"#121212" if st.session_state.theme=="dark" else "#f8f9fa"} !important;
    padding: 1rem;
}}
.sidebar-logo {{
    text-align: center;
    margin-bottom: 10px;
}}
.sidebar-section {{
    background: {"rgba(40,40,40,0.9)" if st.session_state.theme=="dark" else "rgba(255,255,255,0.7)"};
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
    border: 1px solid {"#2a2a2a" if st.session_state.theme=="dark" else "rgba(29, 91, 121, 0.2)"};
}}
.sidebar-header {{
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 6px;
    color: {"#3A95FF" if st.session_state.theme=="dark" else "#1D5B79"};
}}
.sidebar-subheader {{
    font-size: 14px;
    font-weight: 600;
    color: {"#3A95FF" if st.session_state.theme=="dark" else "#1D5B79"};
    margin-bottom: 3px;
    padding-left: 5px;
    border-left: 3px solid {"#3A95FF" if st.session_state.theme=="dark" else "#1D5B79"};
}}
.selection-indicator {{
    background: linear-gradient(90deg, rgba(29, 91, 121, 0.1), transparent);
    border-left: 3px solid #1D5B79;
    padding: 6px 10px;
    margin: 3px 0;
    border-radius: 0 5px 5px 0;
    font-size: 0.9rem;
    color: {"white" if st.session_state.theme=="dark" else "#1A1A1A"};
    font-weight: 500;
}}
.section-header {{
    font-size: 28px;
    font-weight: 600;
    margin: 25px 0 15px;
    padding: 15px;
    background: linear-gradient(to right, rgba(46,139,87,0.1), transparent);
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SQL CONNECTION FUNCTIONS
# =============================================================================
@st.cache_resource
def get_sql_connection():
    """Establish a connection to the SQL Server database."""
    try:
        server = '10.211.10.2'
        database = 'FMS_DB'
        username = 'headofnickel'
        password = 'Dataisbeautifulrev001!'
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
                    'MultipleActiveResultSets=False;'
                )
                conn = pyodbc.connect(conn_str, timeout=30)
                return conn
            except pyodbc.Error:
                continue
    except Exception:
        pass
    return None

@st.cache_data(ttl=300)
def run_sql_query(query, params=None):
    """Execute a SQL query and return a DataFrame."""
    conn = None
    try:
        conn = get_sql_connection()
        if conn is None:
            return pd.DataFrame()
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        return df.copy()
    except Exception:
        return pd.DataFrame()
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

# =============================================================================
# DATA LOADING & INITIALIZATION
# =============================================================================
if "df" not in st.session_state:
    df = get_shared_data()
    if df.empty:
        st.error(get_translation("No data available. Please load your dataset.", st.session_state.language))
        st.stop()
else:
    df = st.session_state.df.copy()

if "Shift Date" in df.columns:
    df["Shift Date"] = pd.to_datetime(df["Shift Date"], errors="coerce")
    df["Shift_Date_only"] = df["Shift Date"].dt.date

# =============================================================================
# SIDEBAR FILTERS (Simplified Version)
# =============================================================================
def render_simplified_sidebar(df: pd.DataFrame) -> dict:
    ASSETS_DIR = Path(__file__).parent.parent / "assets"
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=180)
        st.markdown('</div>', unsafe_allow_html=True)
    
        # Date Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">' + get_translation("Date Selection", st.session_state.language) + '</div>', unsafe_allow_html=True)
        date_selection_type = st.radio(
            get_translation("Select Date Type", st.session_state.language),
            [get_translation("Date Range", st.session_state.language), get_translation("Single Date", st.session_state.language)],
            key="date_selection_type"
        )
        
        # Get min and max date from dataset to ensure we stay within valid range
        min_date = df["Shift_Date_only"].min()
        max_date = df["Shift_Date_only"].max()
        today = date.today()
        
        # Ensure today is not beyond max date
        if today > max_date:
            today = max_date
        
        if date_selection_type == get_translation("Single Date", st.session_state.language):
            selected_date = st.date_input(get_translation("Select Date", st.session_state.language),
                                          value=min(max_date, today),
                                          min_value=min_date,
                                          max_value=max_date,
                                          key="single_date")
            start_date = end_date = selected_date
        else:
            st.markdown('<div class="sidebar-subheader">' + get_translation("Quick Filters", st.session_state.language) + '</div>', unsafe_allow_html=True)
            col_dt1, col_dt2, col_dt3 = st.columns(3)
            
            # Calculate safe default dates that don't exceed dataset bounds
            default_end_date = min(max_date, today)
            default_start_date = max(min_date, default_end_date - timedelta(days=30))
            
            # Initialize date range session state values if not present
            if "quick_filter_start_date" not in st.session_state:
                st.session_state.quick_filter_start_date = default_start_date
            if "quick_filter_end_date" not in st.session_state:
                st.session_state.quick_filter_end_date = default_end_date
                
            # Ensure existing session state values are within bounds
            st.session_state.quick_filter_start_date = max(min_date, min(st.session_state.quick_filter_start_date, max_date))
            st.session_state.quick_filter_end_date = max(min_date, min(st.session_state.quick_filter_end_date, max_date))
                
            with col_dt1:
                if st.button("Last 7", key="last_7_days", use_container_width=True):
                    # Calculate last 7 days, but stay within dataset bounds
                    end_date_7d = min(max_date, today)
                    start_date_7d = max(min_date, end_date_7d - timedelta(days=7))
                    st.session_state.quick_filter_start_date = start_date_7d
                    st.session_state.quick_filter_end_date = end_date_7d
                    st.session_state.sidebar_time_period = get_translation("Last 7 Days", st.session_state.language)
            with col_dt2:
                if st.button("Last 30", key="last_30_days", use_container_width=True):
                    # Calculate last 30 days, but stay within dataset bounds
                    end_date_30d = min(max_date, today)
                    start_date_30d = max(min_date, end_date_30d - timedelta(days=30))
                    st.session_state.quick_filter_start_date = start_date_30d
                    st.session_state.quick_filter_end_date = end_date_30d
                    st.session_state.sidebar_time_period = get_translation("Last 30 Days", st.session_state.language)
            with col_dt3:
                if st.button("All Data", key="all_data", use_container_width=True):
                    st.session_state.quick_filter_start_date = min_date
                    st.session_state.quick_filter_end_date = max_date
                    st.session_state.sidebar_time_period = get_translation("Custom", st.session_state.language)
                    
            time_period = st.selectbox(get_translation("Select Time Period", st.session_state.language),
                                       [get_translation("Last 7 Days", st.session_state.language),
                                        get_translation("Last 30 Days", st.session_state.language),
                                        get_translation("Last 90 Days", st.session_state.language),
                                        get_translation("Year to Date", st.session_state.language),
                                        get_translation("Custom", st.session_state.language)],
                                       key="sidebar_time_period")
                                       
            # Set date range based on time period with bounds checking
            if time_period == get_translation("Last 7 Days", st.session_state.language):
                end_date_7d = min(max_date, today)
                start_date_7d = max(min_date, end_date_7d - timedelta(days=7))
                st.session_state.quick_filter_start_date = start_date_7d
                st.session_state.quick_filter_end_date = end_date_7d
            elif time_period == get_translation("Last 30 Days", st.session_state.language):
                end_date_30d = min(max_date, today)
                start_date_30d = max(min_date, end_date_30d - timedelta(days=30))
                st.session_state.quick_filter_start_date = start_date_30d
                st.session_state.quick_filter_end_date = end_date_30d
            elif time_period == get_translation("Last 90 Days", st.session_state.language):
                end_date_90d = min(max_date, today)
                start_date_90d = max(min_date, end_date_90d - timedelta(days=90))
                st.session_state.quick_filter_start_date = start_date_90d
                st.session_state.quick_filter_end_date = end_date_90d
            elif time_period == get_translation("Year to Date", st.session_state.language):
                end_date_ytd = min(max_date, today)
                start_date_ytd = max(min_date, date(today.year, 1, 1))
                st.session_state.quick_filter_start_date = start_date_ytd
                st.session_state.quick_filter_end_date = end_date_ytd
                
            # Use session state values for date inputs, with bounds checking
            st.markdown('<div class="sidebar-subheader">' + get_translation("Start Date", st.session_state.language) + '</div>', unsafe_allow_html=True)
            start_date = st.date_input(get_translation("Custom Start Date", st.session_state.language),
                                       value=st.session_state.quick_filter_start_date,
                                       min_value=min_date,
                                       max_value=max_date,
                                       key="sidebar_custom_start_date")
            st.markdown('<div class="sidebar-subheader">' + get_translation("End Date", st.session_state.language) + '</div>', unsafe_allow_html=True)
            end_date = st.date_input(get_translation("Custom End Date", st.session_state.language),
                                     value=st.session_state.quick_filter_end_date,
                                     min_value=min_date,
                                     max_value=max_date,
                                     key="sidebar_custom_end_date")
                                     
            # Update session state with any manual changes to date inputs
            st.session_state.quick_filter_start_date = start_date
            st.session_state.quick_filter_end_date = end_date
            
            if start_date > end_date:
                start_date, end_date = end_date, start_date
                st.session_state.quick_filter_start_date = start_date
                st.session_state.quick_filter_end_date = end_date
                
        date_display = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        st.markdown(f'<div class="selection-indicator">Selected: {date_display}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
        # Fleet Group
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">' + get_translation("Select Fleet Group", st.session_state.language) + '</div>', unsafe_allow_html=True)
        if "Group" in df.columns:
            available_groups = ["All"] + sorted(df["Group"].unique().tolist())
            selected_group = st.selectbox("", available_groups, key="sidebar_selected_group")
            if selected_group != "All":
                st.markdown(f'<div class="selection-indicator">Selected: {selected_group}</div>', unsafe_allow_html=True)
        else:
            selected_group = "All"
            st.warning(get_translation("No Group information available", st.session_state.language))
        st.markdown('</div>', unsafe_allow_html=True)
    
        # Risk Level
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">' + get_translation("Select Risk Level", st.session_state.language) + '</div>', unsafe_allow_html=True)
        risk_levels = ["All", get_translation("extreme", st.session_state.language),
                       get_translation("high", st.session_state.language),
                       get_translation("medium", st.session_state.language),
                       get_translation("low", st.session_state.language)]
        selected_risk = st.selectbox("", risk_levels, key="sidebar_selected_risk")
        if selected_risk != "All":
            st.markdown(f'<div class="selection-indicator">Selected: {selected_risk}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
        # Shift Selection
        st.markdown('<div class="select-shift">', unsafe_allow_html=True)
        st.markdown('<h3>' + get_translation("Select Shift", st.session_state.language) + '</h3>', unsafe_allow_html=True)
        col_sh1, col_sh2, col_sh3 = st.columns(3)
        with col_sh1:
            if st.button("All", key="shift_all", use_container_width=True):
                st.session_state.selected_shift = "All"
        with col_sh2:
            if st.button("Day", key="shift_day", use_container_width=True):
                st.session_state.selected_shift = "Siang"
        with col_sh3:
            if st.button("Night", key="shift_night", use_container_width=True):
                st.session_state.selected_shift = "Malam"
        selected_shift = st.session_state.get("selected_shift", "All")
        st.markdown(f'<div class="selection-indicator">Selected Shift: {selected_shift}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        "date_type": "single" if date_selection_type == get_translation("Single Date", st.session_state.language) else "range",
        "dates": start_date if date_selection_type == get_translation("Single Date", st.session_state.language) else (start_date, end_date),
        "group": selected_group,
        "risk_level": selected_risk,
        "shift": selected_shift
    }

selections = render_simplified_sidebar(df)
st.session_state.selections = selections

# Replace ambiguous one-liner with an explicit if/else block for filtering by date
if selections.get("dates"):
    d = selections["dates"]
    if isinstance(d, tuple):
        filtered_df = df[(df["Shift_Date_only"] >= d[0]) & (df["Shift_Date_only"] <= d[1])]
    else:
        filtered_df = df[df["Shift_Date_only"] == d]
else:
    filtered_df = df.copy()

dashboard_filtered_df = filtered_df.copy()

if selections.get("dates"):
    if isinstance(selections["dates"], tuple):
        start_date, end_date = selections["dates"]
    else:
        start_date = end_date = selections["dates"]
    def get_previous_period_df(df, start_date, end_date, selections):
        period_days = (end_date - start_date).days if start_date != end_date else 1
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=period_days)
        prev_df = df[(df["Shift_Date_only"] >= prev_start_date) & (df["Shift_Date_only"] <= prev_end_date)]
        if selections.get("group", "All") != "All" and "Group" in prev_df.columns:
            prev_df = prev_df[prev_df["Group"] == selections["group"]]
        if selections.get("risk_level", "All") != "All" and "Risk Level" in prev_df.columns:
            mapping = { get_translation("extreme", "EN"): "Extreme",
                        get_translation("high", "EN"): "High",
                        get_translation("medium", "EN"): "Medium",
                        get_translation("low", "EN"): "Low" }
            risk_level_standard = mapping.get(selections["risk_level"], selections["risk_level"])
            prev_df = prev_df[prev_df["Risk Level"] == risk_level_standard]
        return prev_df
    prev_df = get_previous_period_df(df, start_date, end_date, selections)
else:
    prev_df = df.copy()

# =============================================================================
# KPI METRICS CALCULATION & DISPLAY (with CSS animations preserved)
# =============================================================================
df["Driver"] = df["Driver"].fillna("").astype(str).str.strip()
total_unique_drivers = df[df["Driver"] != ""]["Driver"].nunique()
overspeed_threshold = 6
total_violations = len(filtered_df[filtered_df["Overspeeding Value"] >= overspeed_threshold])
driver_daily_events = filtered_df[
    (filtered_df["Driver"] != "") &
    (filtered_df["Overspeeding Value"] >= overspeed_threshold)
].groupby(["Driver", "Shift_Date_only"]).size().reset_index(name="daily_events")
high_risk_drivers = driver_daily_events[driver_daily_events["daily_events"] > 1]["Driver"].nunique()
active_drivers = filtered_df[(filtered_df["Driver"] != "") & (filtered_df["Overspeeding Value"] >= overspeed_threshold)]["Driver"].nunique()

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="kpi-card blue">
        <div class="kpi-title">{get_translation("total_drivers", st.session_state.language)}</div>
        <div class="kpi-value">{total_unique_drivers}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="kpi-card green">
        <div class="kpi-title">{get_translation("total_over_speeding_violations", st.session_state.language)}</div>
        <div class="kpi-value">{total_violations}</div>
    </div>
    """, unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    total_incidents = len(filtered_df)
    if not prev_df.empty:
        prev_incidents = len(prev_df)
        percent_change = ((total_incidents - prev_incidents) / prev_incidents * 100) if prev_incidents > 0 else 0
        color_class = 'red' if percent_change > 0 else 'green' if percent_change < 0 else 'blue'
    else:
        color_class = 'blue'
    st.markdown(f"""
    <div class="kpi-card {color_class}">
        <div class="kpi-title">{get_translation("Total Incidents", st.session_state.language)}</div>
        <div class="kpi-value">{total_incidents:,}</div>
    </div>
    """, unsafe_allow_html=True)
with kpi2:
    if "Driver" in filtered_df.columns and "Overspeeding Value" in filtered_df.columns:
        high_risk_count = filtered_df[filtered_df["Overspeeding Value"] >= overspeed_threshold]["Driver"].nunique()
        st.markdown(f"""
        <div class="kpi-card red">
            <div class="kpi-title">{get_translation("High Risk Drivers", st.session_state.language)}</div>
            <div class="kpi-value">{high_risk_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="kpi-card red">
            <div class="kpi-title">{get_translation("High Risk Drivers", st.session_state.language)}</div>
            <div class="kpi-value">N/A</div>
        </div>
        """, unsafe_allow_html=True)
with kpi3:
    if "Driver" in filtered_df.columns and "Overspeeding Value" in filtered_df.columns:
        valid_df = filtered_df[(filtered_df["Driver"] != "") & (filtered_df["Overspeeding Value"] > 0)]
        if not valid_df.empty:
            avg_overspeeding = valid_df.groupby("Driver")["Overspeeding Value"].mean().mean()
            if "Driver" in prev_df.columns and "Overspeeding Value" in prev_df.columns:
                valid_prev_df = prev_df[(prev_df["Driver"] != "") & (prev_df["Overspeeding Value"] > 0)]
                if not valid_prev_df.empty:
                    prev_avg = valid_prev_df.groupby("Driver")["Overspeeding Value"].mean().mean()
                    percent_change = ((avg_overspeeding - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
                    color_class = 'red' if percent_change > 0 else 'green' if percent_change < 0 else 'blue'
                else:
                    color_class = 'blue'
            else:
                color_class = 'blue'
            st.markdown(f"""
            <div class="kpi-card {color_class}">
                <div class="kpi-title">{get_translation("Avg Overspeeding/Driver", st.session_state.language)}</div>
                <div class="kpi-value">{int(avg_overspeeding)}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="kpi-card blue">
                <div class="kpi-title">{get_translation("Avg Overspeeding/Driver", st.session_state.language)}</div>
                <div class="kpi-value">N/A</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="kpi-card blue">
            <div class="kpi-title">{get_translation("Avg Overspeeding/Driver", st.session_state.language)}</div>
            <div class="kpi-value">N/A</div>
        </div>
        """, unsafe_allow_html=True)
with kpi4:
    if "Overspeeding Value" in filtered_df.columns:
        extreme_incidents = filtered_df[filtered_df["Overspeeding Value"] >= 20].shape[0]
        st.markdown(f"""
        <div class="kpi-card red">
            <div class="kpi-title">{get_translation("Extreme Risk Events", st.session_state.language)}</div>
            <div class="kpi-value">{extreme_incidents}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="kpi-card red">
            <div class="kpi-title">{get_translation("Extreme Risk Events", st.session_state.language)}</div>
            <div class="kpi-value">N/A</div>
        </div>
        """, unsafe_allow_html=True)
render_glow_line()

# =============================================================================
# PERFORMANCE CHARTS
# =============================================================================
render_chart_title("performance_charts")
col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    if "Shift Date" in filtered_df.columns:
        time_trend = filtered_df.groupby(pd.Grouper(key="Shift Date", freq="D")).size().reset_index(name="count")
        fig_line = px.line(
            time_trend,
            x="Shift Date",
            y="count",
            labels={"Shift Date": get_translation("Date", st.session_state.language),
                    "count": get_translation("Number of Incidents", st.session_state.language)},
            title=get_translation("Daily Incident Trend", st.session_state.language)
        )
        fig_line.update_traces(line=dict(width=3, color="#1D5B79"), mode="lines+markers",
                               marker=dict(size=8, line=dict(width=1, color="#2E8B57")))
        fig_line.update_layout(height=400, template="plotly_white",
                               title_font=dict(size=20, family="Arial", color="#2a3f5f"),
                               xaxis_title=get_translation("Date", st.session_state.language),
                               yaxis_title=get_translation("Number of Incidents", st.session_state.language),
                               plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                               xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)'),
                               yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)'))
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning(get_translation("Date information is not available in the data", st.session_state.language))
with col_chart2:
    if "Overspeeding Value" in filtered_df.columns:
        filtered_df['Speed Category'] = pd.cut(
            filtered_df['Overspeeding Value'],
            bins=[0, 10, 20, float('inf')],
            labels=[get_translation("0-10 km/h", st.session_state.language),
                    get_translation("10-20 km/h", st.session_state.language),
                    get_translation("20+ km/h", st.session_state.language)],
            include_lowest=True
        )
        speed_counts = filtered_df['Speed Category'].value_counts().reset_index()
        speed_counts.columns = [get_translation("Speed Category", st.session_state.language), get_translation("Count", st.session_state.language)]
        speed_colors = {
            get_translation("0-10 km/h", st.session_state.language): "#FFD700",
            get_translation("10-20 km/h", st.session_state.language): "#FFA500",
            get_translation("20+ km/h", st.session_state.language): "#FF0000"
        }
        fig_pie = px.pie(
            speed_counts,
            values="Count",
            names=get_translation("Speed Category", st.session_state.language),
            title=get_translation("Incidents by Overspeeding Severity", st.session_state.language),
            color=get_translation("Speed Category", st.session_state.language),
            color_discrete_map=speed_colors,
            hole=0.4
        )
        fig_pie.update_traces(textinfo="percent+label", textfont_size=14,
                                marker=dict(line=dict(color="#FFFFFF", width=2)))
        fig_pie.update_layout(height=400, template="plotly_white",
                              title_font=dict(size=20, family="Arial", color="#2a3f5f"),
                              legend_title=get_translation("Overspeeding Severity", st.session_state.language),
                              plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning(get_translation("Overspeeding value information is not available in the data", st.session_state.language))
render_glow_line()

# =============================================================================
# TOP RISKY DRIVERS & WARNING LETTERS
# =============================================================================
render_chart_title("top_10_risky_drivers")
driver_stats = filtered_df[filtered_df["Driver"].str.strip() != ""].groupby("Driver")["Overspeeding Value"].mean().reset_index()
top_drivers = driver_stats.sort_values("Overspeeding Value", ascending=False).head(10)
fig_bar = px.bar(top_drivers, y="Driver", x="Overspeeding Value", 
                 title=get_translation("top_10_risky_drivers", st.session_state.language),
                 color="Overspeeding Value", color_continuous_scale="OrRd",
                 height=500)
fig_bar.update_layout(
    yaxis=dict(title="", tickmode='linear', autorange="reversed"),
    xaxis=dict(title=get_translation("Overspeeding Value", st.session_state.language)),
    margin=dict(l=150)
)
st.plotly_chart(fig_bar, use_container_width=True)

render_glow_line()
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
     padding: 1.5rem; border-radius: 12px; margin: 2rem 0; border-left: 5px solid {header_color};">
    <h2 style="font-size: 36px; font-weight: 700; color: {header_color}; margin: 0; letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;">
        🚗 {get_translation("top_15_drivers_with_max_warning_letters", st.session_state.language)}
    </h2>
</div>
""", unsafe_allow_html=True)
filtered_df["Driver"] = filtered_df["Driver"].fillna("").astype(str).str.strip()
valid_drivers_df = filtered_df[(filtered_df["Overspeeding Value"] >= overspeed_threshold) & (filtered_df["Driver"] != "")]
letters_df = valid_drivers_df.drop_duplicates(subset=["Driver", "Shift_Date_only", "Shift"])
top_letters = letters_df.groupby("Driver").size().reset_index(name="Letters")
top_letters = top_letters.sort_values("Letters", ascending=False).head(15)
fig_top15 = px.bar(
    top_letters,
    y="Driver",
    x="Letters",
    color="Letters",
    color_continuous_scale="oranges",
    title=get_translation("Top_15_drivers_by_warning_letters", st.session_state.language),
    text="Letters",
    height=700
)
fig_top15.update_traces(texttemplate='%{text}', textposition='outside', textfont=dict(size=12))
fig_top15.update_layout(
    title_font=dict(size=24, family="Arial"),
    xaxis_title=get_translation("warning_letters", st.session_state.language),
    yaxis_title="",
    yaxis=dict(tickmode='linear', autorange="reversed"),
    xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
    margin=dict(l=150)
)
st.plotly_chart(fig_top15, use_container_width=True)

# Warning Letters Summary Table
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
     padding: 1.5rem; border-radius: 12px; margin: 2rem 0; border-left: 5px solid #2E8B57;">
    <h2 style="font-size: 36px; font-weight: 700; color: #2E8B57; margin: 0; letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;">
        📝 {get_translation("warning_letters_summary", st.session_state.language)}
    </h2>
</div>
""", unsafe_allow_html=True)
if not filtered_df.empty:
    warnings_df = filtered_df[filtered_df["Overspeeding Value"] >= overspeed_threshold]
    warning_counts = warnings_df.groupby(["Group", "Shift"]).size().reset_index(name="Count")
    warning_counts.rename(columns={
        "Group": get_translation("group", st.session_state.language),
        "Shift": get_translation("shift", st.session_state.language),
        "Count": get_translation("warnings", st.session_state.language)
    }, inplace=True)
    warning_display = warning_counts.set_index([get_translation("group", st.session_state.language), get_translation("shift", st.session_state.language)]).T
    st.dataframe(warning_display, use_container_width=True)
else:
    st.info(get_translation("no_warnings_selected_period", st.session_state.language))
render_glow_line()

# -----------------------------------------------------------------------------
# MAILMERGE & PDF GENERATION FUNCTIONS
# -----------------------------------------------------------------------------
def mailmerge_multiple_records(records, template_path="assets/warning_letter.docx", batch_size=None, progress_callback=None):
    """
    Generate a mail merge document with multiple records, optionally in batches with progress updates.
    
    Args:
        records: DataFrame containing the records to mail merge
        template_path: Path to the docx template
        batch_size: Number of records to process in each batch (None = all at once)
        progress_callback: Function to call with progress updates (percent, status message)
        
    Returns:
        A MailMerge document object or list of PDF data depending on mode
    """
    document = MailMerge(template_path)
    dict_list = []
    
    total_records = len(records)
    processed = 0
    
    # Process records in smaller chunks if batch_size is specified
    for idx, (_, row) in enumerate(records.iterrows()):
        start_time_raw = row.get("Start Time", "")
        try:
            dt_obj = pd.to_datetime(start_time_raw)
            incident_date = dt_obj.strftime("%Y-%m-%d")
            incident_time = dt_obj.strftime("%H:%M:%S")
        except Exception:
            incident_date = str(start_time_raw)
            incident_time = str(start_time_raw)
        dict_item = {
            "Driver_ID": str(row.get("Driver ID", "N/A")),
            "Driver": str(row.get("Driver", "Unknown Driver")).strip(),
            "Group": str(row.get("Group", "Unknown Department")),
            "Start_Time": incident_time,
            "Shift_Date": incident_date,
            "Area": str(row.get("Area", "Unknown Location")),
            "Overspeeding_Value": str(row.get("Overspeeding Value", 0)),
            "Speed_Limit": str(row.get("Speed Limit", "N/A")),
            "Shift": str(row.get("Shift", "N/A")),
            "Max_Speedkmh": str(row.get("Max Speed(Km/h)", "N/A")),
            "License_Plate": str(row.get("License Plate", "N/A"))
        }
        dict_list.append(dict_item)
        
        processed += 1
        if progress_callback and total_records > 0:
            # Calculate and report progress for data preparation phase
            progress_pct = (processed / total_records) * 40  # Data prep is 40% of the process
            remaining_records = total_records - processed
            progress_callback(progress_pct, f"Preparing data: {processed}/{total_records} records ({remaining_records} remaining)")
    
    if dict_list:
        if progress_callback:
            progress_callback(40, "Starting mail merge...")
        
        # If we're using batches, we'll merge in chunks
        if batch_size and batch_size < len(dict_list):
            batch_count = (len(dict_list) + batch_size - 1) // batch_size  # Ceiling division
            merged_docs = []
            
            for i in range(0, len(dict_list), batch_size):
                batch = dict_list[i:i+batch_size]
                batch_doc = MailMerge(template_path)
                batch_doc.merge_pages(batch)
                merged_docs.append(batch_doc)
                
                if progress_callback:
                    batch_num = i // batch_size + 1
                    progress_pct = 40 + (batch_num / batch_count) * 20  # Merging is 20% of process
                    progress_callback(progress_pct, f"Mail merging batch {batch_num}/{batch_count}")
            
            if progress_callback:
                progress_callback(60, "Mail merge complete, preparing for PDF conversion")
            return merged_docs
        else:
            # Process all at once
            if progress_callback:
                progress_callback(50, f"Mail merging {len(dict_list)} records...")
            document.merge_pages(dict_list)
            if progress_callback:
                progress_callback(60, "Mail merge complete, preparing for PDF conversion")
            return document
    return document

def convert_mailmerged_doc_to_pdf(mailmerge_doc_or_list, progress_callback=None):
    """
    Convert MailMerge document(s) to PDF
    
    Args:
        mailmerge_doc_or_list: Either a MailMerge document or a list of MailMerge documents
        progress_callback: Function to call with progress updates (percent, status message)
    
    Returns:
        PDF data as bytes
    """
    # Convert a single document
    if not isinstance(mailmerge_doc_or_list, list):
        mailmerge_doc_or_list = [mailmerge_doc_or_list]
    
    # Multiple documents - convert each separately then merge
    all_pdf_paths = []
    pythoncom.CoInitialize()
    
    try:
        temp_dir = tempfile.gettempdir()
        master_pdf_path = os.path.join(temp_dir, f"warning_letters_master_{str(uuid.uuid4())}.pdf")
        
        # Process each document in the list
        for idx, doc in enumerate(mailmerge_doc_or_list):
            temp_id = str(uuid.uuid4())
            output_path_docx = os.path.join(temp_dir, f"warning_letter_{temp_id}.docx")
            output_path_pdf = os.path.join(temp_dir, f"warning_letter_{temp_id}.pdf")
            all_pdf_paths.append(output_path_pdf)
            
            try:
                # Write the doc to a temporary file
                doc.write(output_path_docx)
                
                # Convert to PDF
                if progress_callback:
                    batch_progress = 60 + ((idx+1) / len(mailmerge_doc_or_list)) * 30
                    progress_callback(batch_progress, f"Converting batch {idx+1}/{len(mailmerge_doc_or_list)} to PDF")
                
                docx2pdf_convert(output_path_docx, output_path_pdf)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(60, f"Error converting batch {idx+1}: {str(e)}")
                raise
        
        # Merge all PDFs into one file
        if all_pdf_paths:
            if progress_callback:
                progress_callback(90, f"Merging {len(all_pdf_paths)} PDF files...")
            
            merger = PyPDF2.PdfMerger()
            for pdf_path in all_pdf_paths:
                merger.append(pdf_path)
            
            merger.write(master_pdf_path)
            merger.close()
            
            with open(master_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            if progress_callback:
                progress_callback(95, "PDF merge complete, preparing download")
            
            return pdf_bytes
        
    finally:
        pythoncom.CoUninitialize()
        # Clean up all temporary files
        for path in all_pdf_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                if progress_callback:
                    progress_callback(98, f"Warning: Could not clean up temporary file: {e}")
        
        # Clean up merged PDF
        try:
            if os.path.exists(master_pdf_path):
                os.remove(master_pdf_path)
        except Exception:
            pass
            
        # Clean up temp docx files
        docx_pattern = os.path.join(temp_dir, "warning_letter_*.docx")
        import glob
        for docx_file in glob.glob(docx_pattern):
            try:
                os.remove(docx_file)
            except Exception:
                pass

def estimate_processing_time(num_records, batch_size=None):
    """
    Estimate the time needed to process records based on record count.
    These numbers are approximate and should be tuned based on actual performance.
    
    Args:
        num_records: Number of records to process
        batch_size: Batch size (or None if not batching)
    
    Returns:
        Estimated time in seconds
    """
    # These are example coefficients - adjust based on your actual system performance
    if batch_size and batch_size < num_records:
        # Processing in batches is usually more efficient for large datasets
        num_batches = (num_records + batch_size - 1) // batch_size
        return 3 + (0.5 * num_records) + (5 * num_batches)  # Base time + per record + per batch
    else:
        # Single batch processing
        return 5 + (0.8 * num_records)  # Base time + per record time

# -----------------------------------------------------------------------------
# OVERSPEEDING WARNING LETTERS SECTION
# -----------------------------------------------------------------------------
def overspeeding_warning_letters(df: pd.DataFrame):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
         padding: 1.5rem; border-radius: 12px; margin: 2rem 0; border-left: 5px solid #1D5B79;">
        <h2 style="font-size: 36px; font-weight: 700; color: #1D5B79; margin: 0; letter-spacing: 0.5px;
            font-family: 'Segoe UI', Arial, sans-serif; display: flex; align-items: center; gap: 10px;">
            ⚠️ {get_translation("overspeeding_violations", st.session_state.language)}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    if "selections" not in st.session_state:
        st.error(get_translation("No sidebar selections found!", st.session_state.language))
        return
    selections = st.session_state["selections"]
    if selections.get("date_type") == "single":
        selected_date = selections.get("dates")
        date_display = f"**{get_translation('Selected Date', st.session_state.language)}:** {selected_date}"
        start_date = end_date = selected_date
    else:
        start_date, end_date = selections.get("dates", (None, None))
        date_display = f"**{get_translation('Selected Date Range', st.session_state.language)}:** {start_date} → {end_date}"
    if not start_date or not end_date:
        st.error(get_translation("Please select a date in the sidebar.", st.session_state.language))
        return
    st.info(date_display)
    
    # Settings for PDF generation
    col_settings1, col_settings2 = st.columns([1, 1])
    with col_settings1:
        overspeed_threshold_input = st.number_input(
            get_translation("overspeeding_threshold", st.session_state.language),
            min_value=1, value=6, key="overspeed_threshold_warning"
        )
    with col_settings2:
        use_batching = st.checkbox(get_translation("Process in batches (recommended for large datasets)", st.session_state.language), value=True)
        if use_batching:
            batch_size = st.slider(get_translation("Batch size", st.session_state.language), min_value=10, max_value=100, value=25, step=5)
        else:
            batch_size = None
    
    required_cols = ["Shift Date", "Overspeeding Value", "Driver", "License Plate", "Shift", "Start Time"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"{get_translation('Missing required columns', st.session_state.language)}: {missing_cols}")
        st.stop()
    df["Shift_Date_only"] = pd.to_datetime(df["Shift Date"]).dt.date
    df["Driver"] = df["Driver"].fillna("").astype(str).str.strip()
    df["License Plate"] = df["License Plate"].fillna("").astype(str).str.strip()
    # Apply date filtering based on whether a single date or a range was selected
    if start_date == end_date:
        filtered = df[df["Shift_Date_only"] == start_date]
    else:
        filtered = df[(df["Shift_Date_only"] >= start_date) & (df["Shift_Date_only"] <= end_date)]
    filtered = filtered[filtered["Overspeeding Value"] >= overspeed_threshold_input]
    if st.button(get_translation("check_over_speeding", st.session_state.language)):
        st.session_state["named_drivers"] = filtered[filtered["Driver"] != ""].drop_duplicates(subset=["Driver", "Shift_Date_only"])
        st.session_state["unnamed_drivers"] = filtered[filtered["Driver"] == ""].drop_duplicates(subset=["License Plate", "Shift_Date_only", "Shift"])
        st.session_state["show_summary"] = True
    if "show_summary" in st.session_state:
        named_drivers = st.session_state.get("named_drivers", pd.DataFrame())
        unnamed_drivers = st.session_state.get("unnamed_drivers", pd.DataFrame())
        total_violations_filtered = len(filtered)
        named_count = len(named_drivers)
        unnamed_count = len(unnamed_drivers)
        total_letters = named_count + unnamed_count
        st.markdown("""
            <style>
                .summary-container {
                    background: white !important;
                    padding: 25px !important;
                    border-radius: 12px !important;
                    border: 2px solid rgba(46, 139, 87, 0.1) !important;
                    margin: 25px 0 !important;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
                    transition: all 0.3s ease !important;
                }
                .summary-title {
                    font-size: 28px !important;
                    font-weight: 600 !important;
                    color: #1D5B79 !important;
                    margin-bottom: 20px !important;
                    padding-bottom: 10px !important;
                    border-bottom: 2px solid rgba(46, 139, 87, 0.2) !important;
                    display: flex !important;
                    align-items: center !important;
                    gap: 10px !important;
                }
                .summary-item {
                    font-size: 18px !important;
                    font-weight: 500 !important;
                    color: #2a3f5f !important;
                    margin-bottom: 12px !important;
                    padding: 12px !important;
                    border-radius: 8px !important;
                    background: rgba(46, 139, 87, 0.05) !important;
                    display: flex !important;
                    justify-content: space-between !important;
                    align-items: center !important;
                    transition: all 0.2s ease !important;
                }
                .summary-item:hover {
                    background: rgba(46, 139, 87, 0.1) !important;
                    transform: translateX(5px) !important;
                }
                .summary-value {
                    font-size: 22px !important;
                    font-weight: 600 !important;
                    color: #2E8B57 !important;
                    padding: 4px 12px !important;
                    border-radius: 4px !important;
                    background: rgba(46, 139, 87, 0.1) !important;
                }
            </style>
        """, unsafe_allow_html=True)
        st.markdown(f"""
            <div class="summary-container">
                <div class="summary-title">{get_translation("summary_title", st.session_state.language)}</div>
                <div class="summary-item">{get_translation("violations_in_range", st.session_state.language)} <span class="summary-value">{total_violations_filtered}</span></div>
                <div class="summary-item">{get_translation("named_drivers", st.session_state.language)} <span class="summary-value">{named_count}</span></div>
                <div class="summary-item">{get_translation("unnamed_drivers", st.session_state.language)} <span class="summary-value">{unnamed_count}</span></div>
                <div class="summary-item">{get_translation("total_warning_letters", st.session_state.language)} <span class="summary-value">{total_letters}</span></div>
            </div>
        """, unsafe_allow_html=True)
        
        # If we have data, show estimated processing time
        if named_count > 0:
            named_est_time = estimate_processing_time(named_count, batch_size if use_batching else None)
            named_time_str = f"({get_translation('Est. time', st.session_state.language)}: {named_est_time:.1f}s)" if named_count > 0 else ""
        else:
            named_time_str = ""
            
        if unnamed_count > 0:
            unnamed_est_time = estimate_processing_time(unnamed_count, batch_size if use_batching else None)
            unnamed_time_str = f"({get_translation('Est. time', st.session_state.language)}: {unnamed_est_time:.1f}s)" if unnamed_count > 0 else ""
        else:
            unnamed_time_str = ""
            
        col_pdf_named, col_pdf_unnamed = st.columns(2)
        with col_pdf_named:
            if st.button(f"{get_translation('generate_pdf_named', st.session_state.language)} {named_time_str}"):
                if not named_drivers.empty:
                    progress_bar = st.progress(0)
                    status_container = st.empty()
                    time_container = st.empty()
                    total_drivers = len(named_drivers)
                    start_time_pdf = time.time()
                    
                    # Define progress callback
                    def update_progress(percent, message):
                        progress_bar.progress(int(percent))
                        status_container.info(message)
                        elapsed = time.time() - start_time_pdf
                        if percent < 98:  # Don't estimate remaining time when almost done
                            estimated_total = elapsed / (percent/100) if percent > 0 else 0
                            remaining = max(0, estimated_total - elapsed)
                            time_container.info(f"⏱️ {get_translation('Time elapsed', st.session_state.language)}: {elapsed:.1f}s - {get_translation('Estimated remaining', st.session_state.language)}: {remaining:.1f}s")
                    
                    with st.spinner(get_translation("generating_pdf", st.session_state.language)):
                        # Initialize with estimate
                        update_progress(1, f"{get_translation('Starting PDF generation for', st.session_state.language)} {total_drivers} {get_translation('named drivers', st.session_state.language)}...")
                        
                        # Process in batches if needed
                        batch_size_to_use = batch_size if use_batching else None
                        doc_merged = mailmerge_multiple_records(
                            named_drivers, 
                            batch_size=batch_size_to_use,
                            progress_callback=update_progress
                        )
                        
                        # Convert to PDF
                        pdf_bytes = convert_mailmerged_doc_to_pdf(doc_merged, progress_callback=update_progress)
                        
                        # Complete
                        elapsed = time.time() - start_time_pdf
                        progress_bar.progress(100)
                        status_container.success(get_translation("pdf_generation_complete", st.session_state.language) + f" ({elapsed:.1f}s)")
                        time_container.empty()  # Clear the time estimate
                    
                    st.download_button(get_translation("download_pdf_named", st.session_state.language),
                                       pdf_bytes, "warning_letters_named.pdf", "application/pdf")
                else:
                    st.warning(get_translation("no_named_drivers", st.session_state.language))
        
        with col_pdf_unnamed:
            if st.button(f"{get_translation('generate_pdf_unnamed', st.session_state.language)} {unnamed_time_str}"):
                if not unnamed_drivers.empty:
                    progress_bar = st.progress(0)
                    status_container = st.empty()
                    time_container = st.empty()
                    total_drivers = len(unnamed_drivers)
                    start_time_pdf = time.time()
                    
                    # Define progress callback
                    def update_progress(percent, message):
                        progress_bar.progress(int(percent))
                        status_container.info(message)
                        elapsed = time.time() - start_time_pdf
                        if percent < 98:  # Don't estimate remaining time when almost done
                            estimated_total = elapsed / (percent/100) if percent > 0 else 0
                            remaining = max(0, estimated_total - elapsed)
                            time_container.info(f"⏱️ {get_translation('Time elapsed', st.session_state.language)}: {elapsed:.1f}s - {get_translation('Estimated remaining', st.session_state.language)}: {remaining:.1f}s")
                    
                    with st.spinner(get_translation("generating_pdf", st.session_state.language)):
                        # Initialize with estimate
                        update_progress(1, f"{get_translation('Starting PDF generation for', st.session_state.language)} {total_drivers} {get_translation('unnamed drivers', st.session_state.language)}...")
                        
                        # Process in batches if needed
                        batch_size_to_use = batch_size if use_batching else None
                        doc_merged = mailmerge_multiple_records(
                            unnamed_drivers, 
                            batch_size=batch_size_to_use,
                            progress_callback=update_progress
                        )
                        
                        # Convert to PDF
                        pdf_bytes = convert_mailmerged_doc_to_pdf(doc_merged, progress_callback=update_progress)
                        
                        # Complete
                        elapsed = time.time() - start_time_pdf
                        progress_bar.progress(100)
                        status_container.success(get_translation("pdf_generation_complete", st.session_state.language) + f" ({elapsed:.1f}s)")
                        time_container.empty()  # Clear the time estimate
                    
                    st.download_button(get_translation("download_pdf_unnamed", st.session_state.language),
                                       pdf_bytes, "warning_letters_unnamed.pdf", "application/pdf")
                else:
                    st.warning(get_translation("no_unnamed_drivers", st.session_state.language))
    render_glow_line()

if "df" in st.session_state and not st.session_state.df.empty:
    overspeeding_warning_letters(st.session_state.df)
else:
    st.error(get_translation("No data available. Please load your dataset.", st.session_state.language))

# -----------------------------------------------------------------------------
# DRIVER EVENT ANALYSIS SECTION
# -----------------------------------------------------------------------------
heading_bg = "rgba(41, 128, 185, 0.05)" if st.session_state.theme == "light" else "rgba(41, 128, 185, 0.15)"
heading_border = "#2980B9" if st.session_state.theme == "light" else "#4DA9FF"
heading_text = "#2980B9" if st.session_state.theme == "light" else "#4DA9FF"

st.markdown(f"""
<div style="background: linear-gradient(135deg, {heading_bg}, {heading_bg});
     padding: 1.5rem; border-radius: 12px; margin: 2rem 0; border-left: 5px solid {heading_border};">
    <h2 style="font-size: 36px; font-weight: 700; color: {heading_text}; margin: 0; letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;">
        📊 {get_translation("driver_event_analysis", st.session_state.language)}
    </h2>
</div>
""", unsafe_allow_html=True)

driver_list = sorted(filtered_df[filtered_df["Overspeeding Value"] >= overspeed_threshold]["Driver"].unique())
selected_driver = st.selectbox(get_translation("select_driver", st.session_state.language), driver_list)
if selected_driver:
    driver_data = filtered_df[filtered_df["Driver"] == selected_driver]
    event_counts = driver_data["Event Type"].value_counts().reset_index()
    event_counts.columns = [get_translation("event_type", st.session_state.language), get_translation("count", st.session_state.language)]
    st.markdown(f"""<div class="section-header"> {get_translation('event_breakdown_for', st.session_state.language)} {selected_driver}</div>""", unsafe_allow_html=True)
    st.dataframe(event_counts, use_container_width=True)


# =============================================================================
# ADDITIONAL CSS OVERRIDES (if needed)
# =============================================================================
st.markdown("""
<style>
    .section-header { 
        font-size: 28px; 
        font-weight: 600; 
        letter-spacing: 0.5px; 
        margin: 25px 0 15px; 
        padding: 15px;
        background: linear-gradient(to right, rgba(46,139,87,0.1), transparent); 
        border-radius: 8px; 
    }
</style>
""", unsafe_allow_html=True)

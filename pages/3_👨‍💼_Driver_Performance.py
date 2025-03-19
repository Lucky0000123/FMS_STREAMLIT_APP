# Import streamlit first
import streamlit as st

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="Driver Performance & Warning Letters",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import tempfile
import pythoncom
import datetime
from docx2pdf import convert as docx2pdf_convert
from mailmerge import MailMerge
from io import BytesIO
from streamlit_lottie import st_lottie
import json
from utils import (
    render_glow_line,
    load_data,
    switch_theme,
    render_chart_title,
    get_shared_data,
    filter_data,
    clear_shared_data
)
from sidebar import render_sidebar
from translations import (
    get_translation,
    get_event_translation
)
from config import (
    THEME_CONFIG,
    RISK_THRESHOLDS,
    UPLOAD_CONFIG,
    PDF_CONFIG,
    DB_CONFIG,
    GLOBAL_CSS
)
import time
from pathlib import Path
import uuid

# Add custom CSS for KPI cards
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(145deg, #ffffff, #f5f7fa);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin: 12px;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .kpi-title {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1.2;
        margin: 10px 0;
    }
    
    .kpi-card.blue {
        background: linear-gradient(145deg, #ffffff, #f0f7ff);
    }
    
    .kpi-card.red {
        background: linear-gradient(145deg, #ffffff, #fff5f5);
    }
    
    .kpi-card.green {
        background: linear-gradient(145deg, #ffffff, #f0fff4);
    }
    
    .kpi-card.blue .kpi-value {
        color: #2575fc;
    }
    
    .kpi-card.red .kpi-value {
        color: #ff416c;
    }
    
    .kpi-card.green .kpi-value {
        color: #00c6ff;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        transition: all 0.3s ease;
    }
    
    .kpi-card.blue::before {
        background: linear-gradient(180deg, #2575fc, #1a5fc9);
    }
    
    .kpi-card.red::before {
        background: linear-gradient(180deg, #ff416c, #cc3356);
    }
    
    .kpi-card.green::before {
        background: linear-gradient(180deg, #00c6ff, #0098cc);
    }
    
    .kpi-card:hover::before {
        width: 100%;
        opacity: 0.05;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------
# LANGUAGE TOGGLE AND ANIMATION
# --------------------------------------------------------------------
if "language" not in st.session_state:
    st.session_state["language"] = "EN"

def toggle_language():
    st.session_state["language"] = "ZH" if st.session_state["language"] == "EN" else "EN"

# Create a row with two columns for the translation button and JSON animation
col_trans, col_json = st.columns([1, 1])

with col_trans:
    st.markdown("""
    <div style="
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
        text-align: center;
        background: linear-gradient(to right, rgba(29, 91, 121, 0.05), transparent);
    ">
        <h3 style="
            color: #1D5B79;
            margin-bottom: 15px;
            font-size: 32px;
            font-weight: 600;
            letter-spacing: 0.5px;
        ">{}</h3>
    </div>
    """.format(get_translation("click_for_translation", st.session_state.language)), unsafe_allow_html=True)
    
    translation_label = "切换中文" if st.session_state["language"] == "EN" else "Switch to English"
st.button(translation_label, on_click=toggle_language)

with col_json:
    try:
        # Load the animation JSON file
        with open("assets/ani6.json", "r") as f:
            animation_data = json.load(f)
        
        # Display the animation
        st_lottie(
            animation_data,
            speed=1,
            reverse=False,
            loop=True,
            quality="high",
            height=150
        )
    except Exception as e:
        st.warning("Animation could not be loaded. Please ensure the JSON file exists in the assets folder.")

# Add space after the row
st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------------------
# TRANSLATION HELPER
# --------------------------------------------------------------------
def t(en_text, zh_text):
    return zh_text if st.session_state["language"] == "ZH" else en_text

render_glow_line()

# --------------------------------------------------------------------
# PAGE TITLE AND HEADER STYLING
# --------------------------------------------------------------------
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(29, 91, 121, 0.1), rgba(46, 139, 87, 0.1));
    padding: 2rem;
    border-radius: 15px;
    margin: 1rem 0 2rem 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
">
    <h1 style="
        font-size: 48px;
        font-weight: 800;
        background: linear-gradient(135deg, #1D5B79, #2E8B57);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0;
        padding: 10px;
        letter-spacing: 1px;
        font-family: 'Segoe UI', Arial, sans-serif;
    ">{get_translation("driver_performance_title", st.session_state.language)}</h1>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------------------
if "df" not in st.session_state:
    # Create a container for the loading animation
    loading_container = st.empty()
    
    # Show loading animation in the container
    with loading_container:
        st.markdown("""
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
        """, unsafe_allow_html=True)
        
    # Try loading data directly from SQL
    try:
        df = load_data()
        if df is not None and not df.empty:
            st.session_state.df = df
            # Clear the loading animation
            loading_container.empty()
            # Show success message briefly
            success_container = st.empty()
            success_container.success("✅ Data loaded successfully!")
            time.sleep(2)  # Show success message for 2 seconds
            success_container.empty()  # Remove success message
        else:
            loading_container.error(get_translation("no_data_warning", st.session_state.language))
    except Exception as e:
            loading_container.error(f"Error loading data: {str(e)}")

df = st.session_state.df.copy()
df["Shift Date"] = pd.to_datetime(df["Shift Date"]).dt.date

# --------------------------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------------------------
def render_simplified_sidebar(df: pd.DataFrame):
    """Render a simplified sidebar with only logo and date range."""
    with st.sidebar:
        # Logo container with styling
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
        st.image(str(Path("assets/logo.png")), width=250)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Date Range Section with enhanced styling
        st.markdown("""
            <div style="
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                margin: 0.5rem 0;
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(29, 91, 121, 0.1);
            ">
                <div style="
                    color: #1D5B79;
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    padding-bottom: 0.5rem;
                    border-bottom: 2px solid rgba(29, 91, 121, 0.1);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    📅 """ + get_translation("date_range", st.session_state.language) + """
                </div>
        """, unsafe_allow_html=True)
        
        # Get min and max dates from DataFrame
        min_date = pd.to_datetime(df["Shift Date"]).min().date()
        max_date = pd.to_datetime(df["Shift Date"]).max().date()
        
        # Initialize session state for date order if not exists
        if 'date_1' not in st.session_state:
            st.session_state.date_1 = max_date
        if 'date_2' not in st.session_state:
            st.session_state.date_2 = max_date
        
        # Quick selection buttons
        st.markdown("""
            <div style="
                margin-bottom: 15px;
                padding: 10px 0;
            ">
                <div style="color: #1D5B79; margin-bottom: 10px; font-size: 0.9rem;">Quick Selection:</div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        def update_dates(start_date, end_date):
            # Ensure dates are within valid range
            start_date = max(min(start_date, max_date), min_date)
            end_date = max(min(end_date, max_date), min_date)
            st.session_state.date_1 = start_date
            st.session_state.date_2 = end_date
            st.rerun()
        
        # Last Week button
        with col1:
            last_week = max_date - datetime.timedelta(days=7)
            last_week = max(last_week, min_date)  # Ensure last_week is not before min_date
            if st.button("Last Week", use_container_width=True, key="last_week_btn"):
                update_dates(last_week, max_date)
        
        # This Month button
        with col2:
            first_day = max_date.replace(day=1)
            first_day = max(first_day, min_date)  # Ensure first_day is not before min_date
            if st.button("This Month", use_container_width=True, key="this_month_btn"):
                update_dates(first_day, max_date)
            
        # Date inputs
        date_1 = st.date_input(
            "First Date",
            value=st.session_state.date_1,
            min_value=min_date,
            max_value=max_date,
            key="date_input_1"
        )
        
        date_2 = st.date_input(
            "Second Date",
            value=st.session_state.date_2,
            min_value=min_date,
            max_value=max_date,
            key="date_input_2"
        )
        
        # Store the dates in session state
        st.session_state.date_1 = date_1
        st.session_state.date_2 = date_2
        
        # Automatically arrange dates in chronological order
        start_date = min(date_1, date_2)
        end_date = max(date_1, date_2)
        dates = (start_date, end_date)
        
        # Display the arranged dates
        st.markdown(f"""
            <div style="
                margin-top: 15px;
                padding: 10px;
                background: rgba(29, 91, 121, 0.05);
                border-radius: 8px;
                font-size: 0.9rem;
            ">
                <div style="color: #1D5B79; margin-bottom: 5px;">Selected Range:</div>
                <div>Start: {start_date}</div>
                <div>End: {end_date}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add custom styling
        st.markdown("""
        <style>
            /* Remove default sidebar padding and background */
            [data-testid="stSidebar"] {
                background-color: white !important;
                border-right: 1px solid rgba(49, 51, 63, 0.1) !important;
                padding-top: 0 !important;
            }
            
            /* Date Input Styling */
            .stDateInput > div {
                background: white;
                border-radius: 10px !important;
                border: 1px solid rgba(29, 91, 121, 0.2) !important;
                padding: 0.25rem !important;
                width: 100% !important;
            }
            
            .stDateInput > div:hover {
                border-color: #1D5B79 !important;
                box-shadow: 0 0 0 1px rgba(29, 91, 121, 0.2) !important;
            }
            
            .stDateInput > div > div {
                background: transparent !important;
            }
            
            .stDateInput input {
                color: #1D5B79 !important;
                font-weight: 500 !important;
            }
            
            /* Quick Selection Button Styling */
            .stButton > button {
                background: linear-gradient(135deg, #1D5B79, #2E8B57) !important;
                color: white !important;
                border: none !important;
                padding: 0.5rem !important;
                font-size: 0.9rem !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
                width: 100% !important;
            }
            
            .stButton > button:hover {
                opacity: 0.9 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            }
            
            /* Remove any extra padding from the sidebar */
            section[data-testid="stSidebar"] > div {
                padding-top: 0 !important;
            }
            
            /* Ensure the image container has no margins or padding */
            [data-testid="stImage"] {
                margin: 0 auto !important;
                padding: 0 !important;
                display: block !important;
            }
            
            /* Custom scrollbar for sidebar */
            [data-testid="stSidebar"] {
                scrollbar-width: thin;
                scrollbar-color: rgba(29, 91, 121, 0.3) transparent;
            }
            
            [data-testid="stSidebar"]::-webkit-scrollbar {
                width: 6px;
            }
            
            [data-testid="stSidebar"]::-webkit-scrollbar-track {
                background: transparent;
            }
            
            [data-testid="stSidebar"]::-webkit-scrollbar-thumb {
                background-color: rgba(29, 91, 121, 0.3);
                border-radius: 3px;
            }
            
            /* Hide date input label */
            .stDateInput label {
                display: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        return {"dates": dates}

# Replace the existing sidebar code with the simplified version
# --------------------------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------------------------
with st.empty():
    df = get_shared_data()
    if df.empty:
        st.error("⚠️ No data available. Please check the data source.")
        st.stop()

# Apply simplified sidebar
selections = render_simplified_sidebar(df)
filtered_df = filter_data(df, selections)

# Store selections in session state for other components
st.session_state.selections = selections

# --------------------------------------------------------------------
# KPI CARDS
# --------------------------------------------------------------------
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
    padding: 1.5rem;
    border-radius: 12px;
    margin: 2rem 0;
    border-left: 5px solid #1D5B79;
">
    <h2 style="
        font-size: 36px;
        font-weight: 700;
        color: #1D5B79;
        margin: 0;
        padding: 0;
        letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;
    ">📊 {get_translation("performance_overview", st.session_state.language)}</h2>
</div>
""", unsafe_allow_html=True)

# Calculate metrics with improved logic
overspeed_threshold = 6  # Base threshold for violations
events_per_day_threshold = 1  # Threshold for high risk drivers (events per day) - Changed from 3 to 1

# Clean driver names and get total unique drivers (excluding empty/unnamed) - No date filter
df["Driver"] = df["Driver"].fillna("").astype(str).str.strip()
total_unique_drivers = df[df["Driver"] != ""]["Driver"].nunique()

# Get filtered dataframe based on date range
if "selections" in st.session_state and "dates" in st.session_state.selections:
    dates = st.session_state.selections["dates"]
    df["Shift_Date_only"] = pd.to_datetime(df["Shift Date"]).dt.date
    
    # Handle single date selection
    if isinstance(dates, datetime.date):
        # If single date is selected
        filtered_df = df[df["Shift_Date_only"] == dates]
    else:
        # If date range is selected (tuple/list)
        start_date, end_date = dates
        filtered_df = df[
            (df["Shift_Date_only"] >= start_date) &
            (df["Shift_Date_only"] <= end_date)
        ]
else:
    filtered_df = df

# Calculate high risk drivers (more than 3 overspeeding events per day)
# First, get count of overspeeding events per driver per day
driver_daily_events = filtered_df[
    (filtered_df["Driver"] != "") & 
    (filtered_df["Overspeeding Value"] >= overspeed_threshold)
].groupby(["Driver", "Shift_Date_only"]).size().reset_index(name="daily_events")

# Identify drivers who have more than 3 events on any day
high_risk_drivers = driver_daily_events[
    driver_daily_events["daily_events"] > events_per_day_threshold
]["Driver"].nunique()

# Calculate percentage from total unique drivers
high_risk_pct = (high_risk_drivers / total_unique_drivers * 100) if total_unique_drivers > 0 else 0

# Get total number of drivers who had events in this period for context
active_drivers = filtered_df[
    (filtered_df["Driver"] != "") & 
    (filtered_df["Overspeeding Value"] >= overspeed_threshold)
]["Driver"].nunique()

# Total violations in selected date range
total_violations = len(filtered_df[filtered_df["Overspeeding Value"] >= overspeed_threshold])

# Create KPI cards in three columns
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="kpi-card blue">
        <div class="kpi-title">{get_translation("total_drivers", st.session_state.language)}</div>
        <div class="kpi-value">{total_unique_drivers}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card red">
        <div class="kpi-title">{get_translation("high_risk_drivers", st.session_state.language)}</div>
        <div class="kpi-value">{high_risk_pct:.1f}%</div>
        <div style="font-size: 0.8rem; color: #666; text-align: center; margin-top: 5px;">
            {high_risk_drivers} out of {total_unique_drivers} drivers
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card green">
        <div class="kpi-title">{get_translation("total_over_speeding_violations", st.session_state.language)}</div>
        <div class="kpi-value">{total_violations}</div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------
# DRIVER PERFORMANCE CHARTS
# --------------------------------------------------------------------
render_glow_line()
render_chart_title("top_10_risky_drivers")

# Top 10 Drivers Chart
driver_stats = filtered_df.groupby("Driver")["Overspeeding Value"].mean().reset_index()
top_drivers = driver_stats.sort_values("Overspeeding Value", ascending=False).head(10)
fig1 = px.bar(top_drivers, x="Driver", y="Overspeeding Value", 
             title=get_translation("top_10_risky_drivers", st.session_state.language),
             color="Overspeeding Value", color_continuous_scale="OrRd")
st.plotly_chart(fig1, use_container_width=True)

# --------------------------------------------------------------------
# TOP 15 DRIVERS BY WARNING LETTERS
# --------------------------------------------------------------------
render_glow_line()
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
    padding: 1.5rem;
    border-radius: 12px;
    margin: 2rem 0;
    border-left: 5px solid #1D5B79;
">
    <h2 style="
        font-size: 36px;
        font-weight: 700;
        color: #1D5B79;
        margin: 0;
        padding: 0;
        letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;
    ">🚗 {get_translation("top_15_drivers_with_max_warning_letters", st.session_state.language)}</h2>
</div>
""", unsafe_allow_html=True)

# Ensure "Driver" column is cleaned and remove blank names
filtered_df["Driver"] = filtered_df["Driver"].fillna("").astype(str).str.strip()
valid_drivers_df = filtered_df[(filtered_df["Overspeeding Value"] >= 6) & (filtered_df["Driver"] != "")]

# Ensure unique warning letters per (Driver, Shift Date, Shift)
letters_df = valid_drivers_df.drop_duplicates(subset=["Driver", "Shift Date", "Shift"])

# Group by Driver and count warning letters
top_letters = letters_df.groupby("Driver").size().reset_index(name="Letters")

# Sort by count and take top 15
top_letters = top_letters.sort_values("Letters", ascending=False).head(15)

# Generate the bar chart with a stylish color palette
fig_top15 = px.bar(
    top_letters,
    x="Driver",
    y="Letters",
    color="Letters",
    color_continuous_scale="oranges",
    title=get_translation("top_15_drivers_by_warning_letters", st.session_state.language),
    text="Letters",
    height=500  # Increased height
)

# Improve layout
fig_top15.update_traces(
    texttemplate='%{text}', 
    textposition='outside',
    textfont=dict(size=12)  # Adjusted text size
)

fig_top15.update_layout(
    title=dict(
        text=get_translation("top_15_drivers_by_warning_letters", st.session_state.language),
        font=dict(size=24, family="Arial", weight="bold"),
        y=0.95
    ),
    xaxis_title=dict(
        text=get_translation("driver", st.session_state.language),
        font=dict(size=16, family="Arial")
    ),
    yaxis_title=dict(
        text=get_translation("warning_letters", st.session_state.language),
        font=dict(size=16, family="Arial")
    )
)

# Update axis properties
fig_top15.update_xaxes(
    title_font=dict(size=14),
    tickfont=dict(size=12)
)
fig_top15.update_yaxes(
    title_font=dict(size=14),
    tickfont=dict(size=12)
)

st.plotly_chart(fig_top15, use_container_width=True)

# --------------------------------------------------------------------
# WARNING LETTERS TABLE (ROW-WISE)
# --------------------------------------------------------------------
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
    padding: 1.5rem;
    border-radius: 12px;
    margin: 2rem 0;
    border-left: 5px solid #2E8B57;
">
    <h2 style="
        font-size: 36px;
        font-weight: 700;
        color: #2E8B57;
        margin: 0;
        padding: 0;
        letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;
    ">📝 {get_translation("warning_letters_summary", st.session_state.language)}</h2>
</div>
""", unsafe_allow_html=True)

if not filtered_df.empty:
    # Only show rows with Overspeed >= 6
    warnings = filtered_df[filtered_df["Overspeeding Value"] >= 6]
    
    # Group by the original English column names
    warning_counts = (
        warnings.groupby(["Group", "Shift"])
        .size()
        .reset_index(name="Count")
    )
    
    # Rename columns for display using your translation function
    warning_counts.rename(
        columns={
            "Group": get_translation("group", st.session_state.language),
            "Shift": get_translation("shift", st.session_state.language),
            "Count": get_translation("warnings", st.session_state.language)
        },
        inplace=True
    )

    # Now that columns are renamed, set them as the index for display
    warning_display = warning_counts.set_index([get_translation("group", st.session_state.language), get_translation("shift", st.session_state.language)]).T
    st.dataframe(warning_display, use_container_width=True)

else:
    st.info(get_translation("no_warnings_selected_period", st.session_state.language))

def mailmerge_multiple_records(records, template_path="assets/warning_letter.docx"):
    document = MailMerge(template_path)
    dict_list = []
    
    for _, row in records.iterrows():
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
    
    if dict_list:
        document.merge_pages(dict_list)
    return document

def convert_mailmerged_doc_to_pdf(mailmerge_doc):
    """
    Convert a mailmerged document to PDF format.
    
    Args:
        mailmerge_doc: The mailmerge document object to convert
        
    Returns:
        bytes: The PDF content as bytes
    """
    # Create unique temporary file names using uuid
    temp_id = str(uuid.uuid4())
    output_path_docx = os.path.join(tempfile.gettempdir(), f"warning_letter_{temp_id}.docx")
    output_path_pdf = os.path.join(tempfile.gettempdir(), f"warning_letter_{temp_id}.pdf")
    
    try:
        # Write the document to temporary DOCX file
        mailmerge_doc.write(output_path_docx)
        
        # Initialize COM for PDF conversion
        pythoncom.CoInitialize()
        try:
            # Convert DOCX to PDF
            docx2pdf_convert(output_path_docx, output_path_pdf)
        finally:
            # Always uninitialize COM
            pythoncom.CoUninitialize()
        
        # Read and return the PDF content
        with open(output_path_pdf, "rb") as f:
            pdf_bytes = f.read()
        return pdf_bytes
    
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(output_path_docx):
                os.remove(output_path_docx)
            if os.path.exists(output_path_pdf):
                os.remove(output_path_pdf)
        except Exception as e:
            st.warning(f"Failed to clean up temporary files: {e}")

def overspeeding_warning_letters(df: pd.DataFrame):
    st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(29, 91, 121, 0.05), rgba(46, 139, 87, 0.05));
    padding: 1.5rem;
    border-radius: 12px;
    margin: 2rem 0;
    border-left: 5px solid #1D5B79;
">
    <h2 style="
        font-size: 36px;
        font-weight: 700;
        color: #1D5B79;
        margin: 0;
        padding: 0;
        letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;
        display: flex;
        align-items: center;
        gap: 10px;
    ">⚠️ {get_translation("overspeeding_violations", st.session_state.language)}</h2>
</div>
""", unsafe_allow_html=True)

    if "selections" not in st.session_state:
        st.error("No sidebar selections found!")
        return

    selections = st.session_state["selections"]
    dates = selections.get("dates", None)
    
    # Handle single date selection
    if isinstance(dates, datetime.date):
        start_date = end_date = dates
        date_display = f"**Selected Date:** {start_date}"
    else:
        # Handle date range
        start_date, end_date = dates
        date_display = f"**Selected Date Range:** {start_date} → {end_date}"
        
    if not dates:
        st.error("Please select a date in the sidebar.")
        return

    st.info(date_display)

    overspeed_threshold = st.number_input(
        get_translation("overspeeding_threshold"),
        min_value=1,
        value=6,
        key="overspeed_threshold_warning"
    )

    required_cols = ["Shift Date", "Overspeeding Value", "Driver", "License Plate", "Shift", "Start Time"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        st.stop()

    df["Shift_Date_only"] = pd.to_datetime(df["Shift Date"]).dt.date
    df["Driver"] = df["Driver"].fillna("").astype(str).str.strip()
    df["License Plate"] = df["License Plate"].fillna("").astype(str).str.strip()

    filtered = df[
        (df["Shift_Date_only"] == start_date if isinstance(dates, datetime.date)
         else (df["Shift_Date_only"] >= start_date) & (df["Shift_Date_only"] <= end_date)) &
        (df["Overspeeding Value"] >= overspeed_threshold)
    ]

    if st.button(get_translation("check_over_speeding")):
        # Don't display the dataframe, just update the session state
        st.session_state["named_drivers"] = filtered[filtered["Driver"] != ""].drop_duplicates(subset=["Driver", "Shift_Date_only"])
        st.session_state["unnamed_drivers"] = filtered[filtered["Driver"] == ""].drop_duplicates(
            subset=["License Plate", "Shift_Date_only", "Shift"]
        )
        st.session_state["show_summary"] = True
    
    # Always show summary if data is available
    if "show_summary" in st.session_state:
        named_drivers = st.session_state.get("named_drivers", pd.DataFrame())
        unnamed_drivers = st.session_state.get("unnamed_drivers", pd.DataFrame())

        total_violations = len(filtered)
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
    .summary-container:hover {
        border-color: rgba(46, 139, 87, 0.3) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08) !important;
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
    <div class="summary-title">📊 Summary of Over-Speeding Letters</div>
    <div class="summary-item">Violations in Range <span class="summary-value">{total_violations}</span></div>
    <div class="summary-item">Named Drivers (session) <span class="summary-value">{named_count}</span></div>
    <div class="summary-item">Unnamed Drivers (session) <span class="summary-value">{unnamed_count}</span></div>
    <div class="summary-item">Total Warning Letters <span class="summary-value">{total_letters}</span></div>
            </div>
""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(get_translation("generate_pdf_named")):
                if not named_drivers.empty:
                    with st.spinner(get_translation("generating_pdf")):
                        time.sleep(1)  # Brief pause to show the spinner
                    doc_merged = mailmerge_multiple_records(named_drivers)
                    pdf_bytes = convert_mailmerged_doc_to_pdf(doc_merged)
                    st.success(get_translation("pdf_generation_complete"))
                    st.download_button(
                        get_translation("download_pdf_named"),
                        pdf_bytes,
                        "warning_letters_named.pdf",
                        "application/pdf"
                            )
                else:
                    st.warning(get_translation("no_named_drivers"))

        with col2:
            if st.button(get_translation("generate_pdf_unnamed")):
                if not unnamed_drivers.empty:
                    with st.spinner(get_translation("generating_pdf")):
                        time.sleep(1)  # Brief pause to show the spinner
                        doc_merged = mailmerge_multiple_records(unnamed_drivers)
                        pdf_bytes = convert_mailmerged_doc_to_pdf(doc_merged)
                    st.success(get_translation("pdf_generation_complete"))
                    st.download_button(
                        get_translation("download_pdf_unnamed"),
                        pdf_bytes,
                        "warning_letters_unnamed.pdf",
                        "application/pdf"
                    )
                else:
                    st.warning(get_translation("no_unnamed_drivers")) 
    render_glow_line()

if "df" in st.session_state and not st.session_state.df.empty:
    overspeeding_warning_letters(st.session_state.df)
else:
    st.error("No data available. Please load your dataset.")

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(41, 128, 185, 0.05), rgba(52, 152, 219, 0.05));
    padding: 1.5rem;
    border-radius: 12px;
    margin: 2rem 0;
    border-left: 5px solid #2980B9;
">
    <h2 style="
        font-size: 36px;
        font-weight: 700;
        color: #2980B9;
        margin: 0;
        padding: 0;
        letter-spacing: 0.5px;
        font-family: 'Segoe UI', Arial, sans-serif;
    ">📊 {get_translation("driver_event_analysis", st.session_state.language)}</h2>
</div>
""", unsafe_allow_html=True)

# Ensure driver names are sorted and unique
driver_list = sorted(filtered_df[filtered_df["Overspeeding Value"] >= 6]["Driver"].astype(str).unique())

selected_driver = st.selectbox(get_translation("select_driver", st.session_state.language), driver_list)

if selected_driver:
    driver_data = filtered_df[filtered_df["Driver"] == selected_driver]
    event_counts = driver_data["Event Type"].value_counts().reset_index()
    event_counts.columns = [get_translation("event_type", st.session_state.language), get_translation("count", st.session_state.language)]

    st.markdown(f"""
<div class="section-header"> {get_translation('event_breakdown_for', st.session_state.language)} {selected_driver}</div>
""", unsafe_allow_html=True)
    st.dataframe(event_counts, use_container_width=True)

# After the KPI cards section, update the CSS
st.markdown("""
<style>
    /* KPI Cards Styling */
    .kpi-card {
        position: relative;
        padding: 24px;
        border-radius: 16px;
        background: linear-gradient(145deg, #ffffff, #f5f7fa);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        margin: 12px;
        border: 1px solid rgba(0, 0, 0, 0.05);
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    .kpi-card:hover::before {
        width: 100%;
        opacity: 0.08;
    }
    .kpi-title {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        margin-bottom: 12px !important;
        color: #64748b !important;
        text-transform: uppercase !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    }
    .kpi-value {
        font-size: 2.4rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    }
    .kpi-card.blue::before {
        background: linear-gradient(180deg, #2575fc, #1a5fc9);
    }
    .kpi-card.red::before {
        background: linear-gradient(180deg, #ff416c, #cc3356);
    }
    .kpi-card.green::before {
        background: linear-gradient(180deg, #00c6ff, #0098cc);
    }
    .kpi-card.blue .kpi-value {
        background: linear-gradient(45deg, #2575fc, #1a5fc9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-card.red .kpi-value {
        background: linear-gradient(45deg, #ff416c, #cc3356);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-card.green .kpi-value {
        background: linear-gradient(45deg, #00c6ff, #0098cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-card .kpi-subtitle {
        font-size: 0.875rem !important;
        color: #94a3b8 !important;
        margin-top: 8px !important;
        font-weight: 400 !important;
        letter-spacing: 0.01em !important;
    }

    /* Section Headers */
    .section-header {
        font-size: 28px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
    }
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        width: 60px;
        height: 3px;
        background: #FF8C42;
    }

    /* Warning Letters Summary */
    .warning-letters-summary {
        font-size: 24px;
        color: #1D5B79;
        margin: 25px 0 15px 0;
        padding: 15px;
        background: linear-gradient(to right, rgba(46, 139, 87, 0.1), transparent);
        border-radius: 8px;
    }

    /* Event Breakdown */
    .event-breakdown {
        font-size: 24px;
        color: #1D5B79;
        margin: 25px 0 15px 0;
        padding: 15px;
        background: linear-gradient(to right, rgba(29, 91, 121, 0.1), transparent);
        border-radius: 8px;
    }

    /* Summary Container */
    .summary-container {
        background: white !important;
        padding: 25px !important;
        border-radius: 12px !important;
        border: 2px solid rgba(46, 139, 87, 0.1) !important;
        margin-bottom: 25px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    }
    .summary-title {
        font-size: 28px !important;
        letter-spacing: 0.5px !important;
    }
    .summary-item {
        font-size: 18px !important;
        letter-spacing: 0.3px !important;
    }
    .summary-value {
        font-size: 22px !important;
        letter-spacing: 0.3px !important;
    }

    /* Dataframe Styling */
    .dataframe {
        border: none !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    .dataframe th {
        font-size: 16px !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
    }
    .dataframe td {
        font-size: 14px !important;
        letter-spacing: 0.2px !important;
    }
    .dataframe tr:hover {
        background-color: rgba(46, 139, 87, 0.05) !important;
    }

    /* Button Styling */
    .stButton > button {
        background-color: #2E8B57 !important;
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #1D5B79 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background-color: #2E8B57 !important;
    }
</style>
""", unsafe_allow_html=True)

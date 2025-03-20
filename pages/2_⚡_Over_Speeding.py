# Standard library imports
import streamlit as st
import time
import json
import pdfkit
import platform

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

# Local imports
from utils import (
    process_dataframe,
    assign_risk_level,
    load_lottie_json,
    render_chart_title,
    render_header,
    filter_data,
    get_shared_data,
    refresh_data_if_needed,
    render_glow_line
)
from translations import get_translation, get_event_translation
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
            height=300
        )
    except Exception as e:
        st.warning(f"Animation could not be loaded. Error: {str(e)}")

# Add space after the row
st.markdown("<br>", unsafe_allow_html=True)

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
        background-color: #1D5B79 !important;
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
    /* Professional Container Styling */
    .pro-container {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(29, 91, 121, 0.1);
    }

    /* Section Headers */
    .section-header {
        color: #1D5B79;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(29, 91, 121, 0.1);
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Rating Items */
    .rating-item {
        display: flex;
        align-items: center;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(145deg, #ffffff, #f5f7fa);
        border-radius: 10px;
        transition: all 0.3s ease;
        border: 1px solid rgba(29, 91, 121, 0.05);
    }
    .rating-item:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }

    /* Speed Indicators */
    .speed-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 15px;
        position: relative;
    }
    .speed-dot::after {
        content: '';
        position: absolute;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: inherit;
        opacity: 0.3;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    .medium { background: #B59B00; }
    .high { background: #FFA500; }
    .extreme { background: #FF0000; }

    /* Filter Controls */
    .filter-control {
        background: white;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
    }

    /* Radio Button Styling */
    .stRadio > label {
        padding: 12px 20px !important;
        background: white !important;
        border-radius: 8px !important;
        border: 1px solid rgba(29, 91, 121, 0.2) !important;
        margin: 5px 0 !important;
        transition: all 0.3s ease !important;
    }
    .stRadio > label:hover {
        background: rgba(29, 91, 121, 0.05) !important;
        border-color: #1D5B79 !important;
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
    st.markdown(f"<div style='text-align: center; color: #666;'>{trend_days} {get_translation('days', lang)}</div>", unsafe_allow_html=True)
    if "trend_days" not in st.session_state:
        st.session_state.trend_days = 7
        trend_days = st.slider("", 7, 30, st.session_state.trend_days, key="trend_days_top")
        st.session_state.trend_days = trend_days

# Create containers for loading states
loading_container = st.empty()
success_container = st.empty()

# -------------------- DATA LOADING --------------------
# Check if we need to refresh data
refresh_data_if_needed()

# Load data using the optimized get_shared_data function
if "df" not in st.session_state:
    # Only show loading animation when actually loading data
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
    
    # Load the data
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
else:
    # If data is already in session state, just use it
    df = st.session_state.df

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
render_chart_title("speeding_events_by_day")

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
                    title_font=dict(size=24, family="Arial Black", color="#2a3f5f"),
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
                        font=dict(size=14, color="black")
                    ),
                    margin=dict(l=20, r=20, t=60, b=80)
                )
                
                # Store the main figure in session state for PDF generation
                st.session_state["main_trend_fig"] = fig1

                # Display the chart
                st.plotly_chart(fig1, use_container_width=True, key="main_speeding_trend")
            else:
                st.warning(get_translation("no_data_warning", lang))
        else:
            st.error(get_translation("column_not_found_error", lang).format(column="Event Type"))
    except Exception as e:
        st.error(get_translation("data_processing_error", lang).format(error=str(e)))
else:
    st.error(get_translation("column_not_found_error", lang).format(column="Shift Date"))


# -------------------- OVERSPEEDING INTENSITY BY GROUP --------------------
render_chart_title("overspeeding_intensity")

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
            
            # Add line traces with area fill instead of bar charts
            for risk_level in bar_colors.keys():
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
                
                # Keep the trend lines
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

            # Add total events trend line
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
                height=450,
                margin=dict(l=20, r=20, t=80, b=50),
                legend=dict(
                    title=get_translation("risk_level", lang),
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=14, color="black")
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hoverlabel=dict(
                    bgcolor="black",
                    font_size=14,
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
                <div style="
                    background: linear-gradient(135deg, rgba(29, 91, 121, 0.1), rgba(46, 139, 87, 0.1));
                    padding: 1.5rem;
                    border-radius: 15px;
                    margin: 1rem 0;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                ">
                    <h2 style="
                        font-size: 28px;
                        font-weight: 700;
                        color: #1D5B79;
                        text-align: center;
                        margin: 0;
                    ">📊 {get_translation("fleet_group", lang)}: {group}</h2>
                </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, key=f"group_chart_{group}")
            group_fig_list.append(fig)
    
    # Store figures in session state
    st.session_state["group_fig_list"] = group_fig_list

else:
    st.warning(get_translation("no_overspeeding_data", lang))



# -------------------- DOWNLOAD PDF BUTTON --------------------
render_chart_title("download_report")

# Add a new function for direct PDF generation using ReportLab
def generate_direct_pdf():
    """Generate PDF report directly using ReportLab - much faster than HTML conversion."""
    import io
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    
    # Create a BytesIO buffer to receive the PDF data
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment
    title_style.textColor = colors.HexColor('#1D5B79')
    
    subtitle_style = styles['Heading2']
    subtitle_style.textColor = colors.HexColor('#2E8B57')
    
    normal_style = styles['Normal']
    
    # Initialize story elements
    elements = []
    
    # Add the title
    elements.append(Paragraph(get_translation("report_title", lang), title_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Add timestamp
    timestamp_style = ParagraphStyle(
        'timestamp',
        parent=normal_style,
        alignment=2,  # Right alignment
        textColor=colors.gray
    )
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", timestamp_style))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Add status message
    elements.append(Paragraph("Generating charts...", normal_style))
    
    # Helper function to convert Plotly figures to images for the PDF
    def add_plotly_figure(fig, caption, width=7*inch):
        try:
            # Convert Plotly figure to PNG image bytes
            img_bytes = fig.to_image(format="png", width=1000, height=600, scale=1.5)
            
            # Create an in-memory image
            img_stream = io.BytesIO(img_bytes)
            img = Image(img_stream, width=width)
            
            # Add caption and image
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph(caption, subtitle_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(img)
            return True
        except Exception as e:
            elements.append(Paragraph(f"Error generating chart: {str(e)}", normal_style))
            return False
    
    # Add charts - main trend chart first
    charts_added = False
    if "main_trend_fig" in st.session_state:
        if add_plotly_figure(st.session_state["main_trend_fig"], "Overall Speeding Trend"):
            charts_added = True
    
    # Add group charts if available
    if 'group_fig_list' in st.session_state and st.session_state['group_fig_list']:
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("Overspeeding by Fleet Group", subtitle_style))
        
        for i, fig in enumerate(st.session_state['group_fig_list'][:3]):
            if add_plotly_figure(fig, f"Fleet Group {i+1}", width=6.5*inch):
                charts_added = True
    
    # If no charts were added, show a message
    if not charts_added:
        elements.append(Spacer(1, inch))
        no_data_style = ParagraphStyle(
            'nodata',
            parent=normal_style,
            alignment=1,  # Center
            textColor=colors.HexColor('#1D5B79'),
            fontSize=14
        )
        elements.append(Paragraph("No data available for the current selection", no_data_style))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("Please adjust your filters or upload data to generate charts.", normal_style))
    
    # Add footer
    elements.append(Spacer(1, 0.5 * inch))
    footer_style = ParagraphStyle(
        'footer',
        parent=normal_style,
        alignment=1,  # Center
        textColor=colors.gray,
        fontSize=8
    )
    elements.append(Paragraph("Generated by FMS Safety Dashboard", footer_style))
    
    # Build the PDF document
    doc.build(elements)
    
    # Get the PDF value from the buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

# Replace the download button section
if st.button(get_translation("generate_pdf", lang), key="generate_pdf"):
    with st.spinner(get_translation("generating_pdf", lang)):
        try:
            start_time = time.time()
            
            # Generate PDF directly without HTML conversion
            pdf_data = generate_direct_pdf()
            
            generation_time = time.time() - start_time
            st.success(f"PDF generated in {generation_time:.1f} seconds!")
            
            # Create download button
            st.download_button(
                label=get_translation("download_pdf", lang),
                data=pdf_data,
                file_name=f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                key="download_pdf"
            )
            
        except Exception as e:
            st.error(f"{get_translation('pdf_error', lang)} {e}")
            st.error("Error details:", e)
            import traceback
            st.code(traceback.format_exc())
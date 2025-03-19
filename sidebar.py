import os
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
from utils import switch_theme
import datetime
from translations import get_translation

def inject_custom_css(css: str) -> None:
    """
    Injects global custom CSS styles into Streamlit.
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def render_sidebar(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Render a stylish, modern sidebar with improved UI components.
    
    Parameters:
        df: Optional DataFrame to use for filtering options. If None, default values will be used.
        
    Returns:
        Dictionary containing the selected filter values.
    """
    ASSETS_DIR = Path(__file__).parent / "assets"

    # Ensure a default theme is set
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    # Light and Dark Theme Colors
    if st.session_state.theme == "dark":
        sidebar_bg = "#121212"
        sidebar_text = "#FFFFFF"
        button_bg = "linear-gradient(145deg, #3A95FF, #4DA9FF)"
        button_hover = "#5DAFFF"
        button_text = "#FFFFFF"
        border_color = "#2E2E2E"
        section_bg = "rgba(40, 40, 40, 0.9)"
        header_border = "#3A95FF"
        divider_color = "#444444"
    else:
        sidebar_bg = "#F8F8F8"
        sidebar_text = "#2E3440"
        button_bg = "linear-gradient(145deg, #1D5B79, #468B97)"
        button_hover = "#468B97"
        button_text = "#FFFFFF"
        border_color = "#D3D3D3"
        section_bg = "rgba(240, 240, 240, 0.95)"
        header_border = "#1D5B79"
        divider_color = "#D3D3D3"

    # Stylish CSS
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

    /* Custom Checkbox & Select */
    .stSelectbox, .stMultiSelect {{
        background: {section_bg} !important;
        border-radius: 8px;
        border: 1px solid {border_color} !important;
        padding: 10px;
    }}
    """
    inject_custom_css(custom_css)

    # Sidebar Content
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
        safety_logo_path = ASSETS_DIR / "logo.png"
        if safety_logo_path.exists():
            st.image(str(safety_logo_path), width=180)
        st.markdown('</div>', unsafe_allow_html=True)

        # Add custom CSS for modern sidebar styling
        st.markdown("""
        <style>
            /* Modern Sidebar Styling */
            .css-1d391kg {
                padding: 1rem;
            }
            
            /* Section Container */
            .sidebar-section {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            /* Section Title */
            .section-title {
                color: #FF8C42;
                font-size: 1rem;
                font-weight: 600;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            /* Filter Pills */
            .filter-pill {
                background: rgba(255, 140, 66, 0.1);
                border-radius: 20px;
                padding: 5px 10px;
                font-size: 0.8rem;
                color: #FF8C42;
                margin: 2px;
                display: inline-block;
            }
            
            /* Active Selection Indicator */
            .selection-indicator {
                background: linear-gradient(90deg, rgba(255,140,66,0.1) 0%, rgba(255,140,66,0) 100%);
                border-left: 3px solid #FF8C42;
                padding: 8px 12px;
                margin: 5px 0;
                border-radius: 0 5px 5px 0;
                font-size: 0.9rem;
            }
            
            /* Custom Button Styling */
            .stButton > button {
                width: 100%;
                border-radius: 8px;
                border: 1px solid rgba(255, 140, 66, 0.2);
                background: rgba(255, 140, 66, 0.1);
                color: #FF8C42;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .stButton > button:hover {
                background: rgba(255, 140, 66, 0.2);
                border-color: #FF8C42;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(255, 140, 66, 0.1);
            }
            
            /* Selectbox Styling */
            .stSelectbox > div > div {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
            
            /* Date Input Styling */
            .stDateInput > div {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
            
            /* Multiselect Styling */
            .stMultiSelect > div > div {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        </style>
        """, unsafe_allow_html=True)

        # Theme Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎨 Theme</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌞 Light", key="light_theme", use_container_width=True):
                st.session_state.theme = "light"
                switch_theme()
        with col2:
            if st.button("🌙 Dark", key="dark_theme", use_container_width=True):
                st.session_state.theme = "dark"
                switch_theme()
        st.markdown(f'<div class="selection-indicator">Current: {st.session_state.theme.capitalize()}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Language Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🌍 Language</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🇬🇧 English", key="english_lang", use_container_width=True):
                st.session_state.language = "EN"
                st.rerun()
        with col2:
            if st.button("🇨🇳 中文", key="chinese_lang", use_container_width=True):
                st.session_state.language = "ZH"
                st.rerun()
        st.markdown(f'<div class="selection-indicator">Current: {"English" if st.session_state.language == "EN" else "中文"}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Date Range Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📅 Date Range</div>', unsafe_allow_html=True)
        
        # Quick filter buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Last Week", key="last_week", use_container_width=True):
                if "Date" in df.columns:
                    today = df["Date"].max()
                    last_week = today - pd.Timedelta(days=7)
                    st.session_state.date_range = (last_week, today)
        with col2:
            if st.button("This Month", key="this_month", use_container_width=True):
                if "Date" in df.columns:
                    today = df["Date"].max()
                    month_start = today.replace(day=1)
                    st.session_state.date_range = (month_start, today)

        # Date range picker
        if "Date" in df.columns:
            min_date = df["Date"].min()
            max_date = df["Date"].max()
            if 'date_range' in st.session_state:
                selected_dates = st.date_input(
                    "Select Date Range",
                    st.session_state.date_range,
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                selected_dates = st.date_input(
                    "Select Date Range",
                    (min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
        st.markdown('</div>', unsafe_allow_html=True)

        # Shift Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⏰ Shift</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("All", key="shift_all", use_container_width=True):
                st.session_state.selected_shift = "All"
        with col2:
            if st.button("Day", key="shift_day", use_container_width=True):
                st.session_state.selected_shift = "Siang"
        with col3:
            if st.button("Night", key="shift_night", use_container_width=True):
                st.session_state.selected_shift = "Malam"
        
        selected_shift = st.session_state.get("selected_shift", "All")
        st.markdown(f'<div class="selection-indicator">Selected: {selected_shift}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # License Plate Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🚛 Vehicle</div>', unsafe_allow_html=True)
        selected_plate = st.selectbox(
            "Select License Plate",
            ["All"] + sorted(df["License Plate"].unique()),
            label_visibility="collapsed"
        )
        if selected_plate != "All":
            st.markdown(f'<div class="selection-indicator">Selected: {selected_plate}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Fleet Group Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🚜 Fleet Groups</div>', unsafe_allow_html=True)
        selected_groups = st.multiselect(
            "Select Fleet Groups",
            sorted(df["Group"].unique()),
            default=list(df["Group"].unique()),
            label_visibility="collapsed"
        )
        if selected_groups:
            st.markdown('<div class="filter-pills-container">', unsafe_allow_html=True)
            for group in selected_groups:
                st.markdown(f'<span class="filter-pill">{group}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Event Types Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚠️ Event Types</div>', unsafe_allow_html=True)
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
        if selected_events:
            st.markdown('<div class="filter-pills-container">', unsafe_allow_html=True)
            for event in selected_events:
                st.markdown(f'<span class="filter-pill">{event}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    return {
        "selected_shift": selected_shift,
        "selected_dates": selected_dates if "selected_dates" in locals() else None,
        "selected_license_plate": selected_plate,
        "selected_groups": selected_groups,
        "selected_events": selected_events
    }

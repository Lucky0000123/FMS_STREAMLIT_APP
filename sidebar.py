import os
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd
from utils import switch_theme  # This function copies the config file and calls st.rerun()
from translations import get_translation  # For any translations you use

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
        header_color  = "#3A95FF"
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
        header_color  = "#1D5B79"
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

def render_sidebar(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Render a stylish, modern sidebar with dynamic theme responsiveness and filtering options.
    
    Parameters:
        df: Optional DataFrame to use for filtering options. If None, an error is shown.
        
    Returns:
        Dictionary containing the selected filter values.
    """
    if df is None:
        st.error("Data is required for sidebar filtering.")
        return {}

    # Ensure a default theme is set in session state
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    # Inject the dynamic CSS for the sidebar
    inject_sidebar_theme_css()

    ASSETS_DIR = Path(__file__).parent / "assets"

    with st.sidebar:
        # Logo Section
        st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=180)
        st.markdown('</div>', unsafe_allow_html=True)

        # Theme Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">🎨 Theme</div>', unsafe_allow_html=True)
        col_theme1, col_theme2 = st.columns(2)
        with col_theme1:
            if st.button("🌞 Light", key="light_theme", use_container_width=True):
                if st.session_state.theme != "light":
                    st.session_state.theme = "light"
                    switch_theme()  # This function should copy the light config and trigger st.rerun()
        with col_theme2:
            if st.button("🌙 Dark", key="dark_theme", use_container_width=True):
                if st.session_state.theme != "dark":
                    st.session_state.theme = "dark"
                    switch_theme()
        st.markdown(
            f'<div class="selection-indicator">Current: {st.session_state.theme.capitalize()}</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Language Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">🌍 Language</div>', unsafe_allow_html=True)
        col_lang1, col_lang2 = st.columns(2)
        with col_lang1:
            if st.button("🇬🇧 English", key="english_lang", use_container_width=True):
                st.session_state.language = "EN"
                st.rerun()
        with col_lang2:
            if st.button("🇨🇳 中文", key="chinese_lang", use_container_width=True):
                st.session_state.language = "ZH"
                st.rerun()
        current_language = "English" if st.session_state.language == "EN" else "中文"
        st.markdown(
            f'<div class="selection-indicator">Current: {current_language}</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Date Range Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">📅 Date Range</div>', unsafe_allow_html=True)
        # Quick Date Range Buttons
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            if st.button("This Week", key="this_week", use_container_width=True):
                today = datetime.datetime.now().date()
                start_of_week = today - datetime.timedelta(days=today.weekday())
                st.session_state.date_range = (start_of_week, today)
        with col_date2:
            if st.button("This Month", key="this_month", use_container_width=True):
                today = datetime.datetime.now().date()
                start_of_month = today.replace(day=1)
                st.session_state.date_range = (start_of_month, today)

        # Date range picker using the 'Date' column (or modify if you use 'Shift Date')
        if "Date" in df.columns:
            min_date = df["Date"].min() if df["Date"].min() is not pd.NaT else datetime.date.today()
            max_date = df["Date"].max() if df["Date"].max() is not pd.NaT else datetime.date.today()
            if "date_range" not in st.session_state:
                st.session_state.date_range = (min_date, max_date)
            current_start, current_end = st.session_state.date_range
            selected_dates = st.date_input(
                "Select Date Range",
                value=(current_start, current_end),
                min_value=min_date,
                max_value=max_date,
                key="date_range_input",
                help="Select start and end dates",
                format="YYYY/MM/DD"
            )
            if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
                start_date, end_date = selected_dates
                if start_date <= end_date:
                    st.session_state.date_range = (start_date, end_date)
            st.markdown(
                f'<div class="selection-indicator">Selected: {st.session_state.date_range[0].strftime("%Y/%m/%d")} to {st.session_state.date_range[1].strftime("%Y/%m/%d")}</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Shift Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">⏰ Shift</div>', unsafe_allow_html=True)
        col_shift1, col_shift2, col_shift3 = st.columns(3)
        if "selected_shift" not in st.session_state:
            st.session_state.selected_shift = "All"
        with col_shift1:
            if st.button("All", key="shift_all", use_container_width=True):
                st.session_state.selected_shift = "All"
        with col_shift2:
            if st.button("Day", key="shift_day", use_container_width=True):
                st.session_state.selected_shift = "Siang"
        with col_shift3:
            if st.button("Night", key="shift_night", use_container_width=True):
                st.session_state.selected_shift = "Malam"
        st.markdown(
            f'<div class="selection-indicator">Selected: {st.session_state.selected_shift}</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # License Plate Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">🚛 Vehicle</div>', unsafe_allow_html=True)
        license_plates = ["All"]
        if "License Plate" in df.columns:
            license_plates += sorted(df["License Plate"].unique())
        selected_plate = st.selectbox(
            "Select License Plate",
            license_plates,
            label_visibility="collapsed"
        )
        if selected_plate != "All":
            st.markdown(
                f'<div class="selection-indicator">Selected: {selected_plate}</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Fleet Groups Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">🚜 Fleet Groups</div>', unsafe_allow_html=True)
        groups_list = []
        if "Group" in df.columns:
            groups_list = sorted(df["Group"].unique())
        selected_groups = st.multiselect(
            "Select Fleet Groups",
            groups_list,
            default=groups_list,
            label_visibility="collapsed"
        )
        if selected_groups:
            pills_html = "".join([f'<span class="selection-indicator">{group}</span>' for group in selected_groups])
            st.markdown(pills_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Event Types Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">⚠️ Event Types</div>', unsafe_allow_html=True)
        default_events = ["Smoking", "Speeding", "Closed Eyes", "Phone", "Yawn"]
        all_events = []
        if "Event Type" in df.columns:
            all_events = sorted(df["Event Type"].unique())
        default_events = [event for event in default_events if event in all_events]
        other_events = [event for event in all_events if event not in default_events]
        final_event_list = default_events + other_events
        selected_events = st.multiselect(
            "Select Event Types",
            options=final_event_list,
            default=default_events,
            label_visibility="collapsed"
        )
        if selected_events:
            pills_html = "".join([f'<span class="selection-indicator">{event}</span>' for event in selected_events])
            st.markdown(pills_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    return {
        "selected_shift": st.session_state.selected_shift,
        "selected_dates": st.session_state.date_range,
        "selected_license_plate": selected_plate,
        "selected_groups": selected_groups,
        "selected_events": selected_events
    }

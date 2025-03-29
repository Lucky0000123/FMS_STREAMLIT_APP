"""Configuration file for the FMS Safety Dashboard."""
import os

# Theme Configuration
THEME_CONFIG = {
    'gradient_start': '#1D5B79',
    'gradient_middle': '#468B97',
    'gradient_end': '#EF6262',
    'text_color': '#2a3f5f',
    'background_color': '#FFFFFF',
    'accent_color': '#FF8C42'
}

# Risk Thresholds
RISK_THRESHOLDS = {
    'Extreme': 20,
    'High': 11,
    'Medium': 6,
    'Low': 0
}

# Upload Configuration
UPLOAD_CONFIG = {
    'allowed_extensions': ['.csv', '.xlsx', '.xls'],
    'max_file_size_mb': 100,
    'required_columns': [
        'Driver',
        'Driver ID',
        'Group',
        'Shift Date',
        'Start Time',
        'Event Type',
        'Overspeeding Value',
        'Speed Limit',
        'License Plate',
        'Shift',
        'Area'
    ],
    'date_columns': ['Shift Date', 'Start Time'],
    'numeric_columns': ['Overspeeding Value', 'Speed Limit'],
    'categorical_columns': ['Driver', 'Group', 'Event Type', 'License Plate', 'Shift', 'Area']
}

# PDF Report Settings
PDF_CONFIG = {
    'page_size': 'A4',
    'margin': 1.0,  # inches
    'font_size': {
        'title': 16,
        'heading': 14,
        'body': 12
    },
    'max_rows_per_page': 30
}

# Database Configuration
DB_CONFIG = {
    'driver': '{ODBC Driver 18 for SQL Server}' if os.environ.get('SQL_SERVER') else '{SQL Server}',
    'server': os.environ.get('SQL_SERVER', 'DESKTOP-JQDJV8F'),
    'database': os.environ.get('SQL_DATABASE', 'FMS_DB'),  # Default to FMS_DB but can be overridden by environment variable
    'trusted_connection': 'yes' if not os.environ.get('SQL_USERNAME') else 'no',
}

# Add username and password if provided in environment variables
if os.environ.get('SQL_USERNAME') and os.environ.get('SQL_PASSWORD'):
    DB_CONFIG['uid'] = os.environ.get('SQL_USERNAME')
    DB_CONFIG['pwd'] = os.environ.get('SQL_PASSWORD')

# Global CSS Styles
GLOBAL_CSS = """
    <style>
    .main {
        background-color: #FAFAFA !important;
    }
    
    .stButton>button {
        background-color: #2a3f5f !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6em 1em !important;
        margin-top: 5px !important;
    }
    
    .stButton>button:hover {
        background-color: #3c5a8f !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .metric-box {
        background: linear-gradient(135deg, #ffffff, #f0f0f0);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        border-left: 5px solid;
        margin-bottom: 20px;
    }
    
    .metric-title {
        font-size: 16px;
        font-weight: 600;
        color: #2a3f5f;
        margin: 0;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        margin: 10px 0;
    }
    </style>
"""

translations = {
    "EN": {
        # ... existing English translations ...
        "event_distribution": "\ud83d\udcca 1. Total Event Distribution by Fleet Group",
        "event_distribution_detailed": "\ud83d\udcca 2. Detailed Event Distribution by Fleet Group",
        "group_comparison": "\ud83d\udcca 3. Total Speeding Events (Percentage and Count)",
        "time_series": "\ud83d\udcc8 4. Average Speeding Values Over Time",
        "geo_analysis": "\ud83c\udf0d Geo-Spatial Analysis Dashboard",
        "scatter_plot_header": "\ud83d\udccd 5. Speeding Events by Location",
        "heatmap": "\ud83d\udd25 6. Speeding Event Heatmap",
        "dynamic_table": "\ud83d\udcca 7. Dynamic Table Viewer",
        "geo_heatmap_header": "\ud83c\udf0d Geo-Spatial Heat Map",
        "top_speeding_vehicles": "\ud83d\ude97 Top 20 Vehicles with Most Speeding Events",
        # ... other translations ...
    },
    "ZH": {
        # ... existing Chinese translations ...
        "event_distribution": "\ud83d\udcca 1. \u6309\u8f66\u961f\u5206\u7ec4\u7684\u603b\u4e8b\u4ef6\u5206\u5e03",
        "event_distribution_detailed": "\ud83d\udcca 2. \u6309\u8f66\u961f\u5206\u7ec4\u7684\u8be6\u7ec6\u4e8b\u4ef6\u5206\u5e03",
        "group_comparison": "\ud83d\udcca 3. \u603b\u8d85\u901f\u4e8b\u4ef6(\u767e\u5206\u6bd4\u548c\u6570\u91cf)",
        "time_series": "\ud83d\udcc8 4. \u5e73\u5747\u8d85\u901f\u503c\u968f\u65f6\u53d8\u5316",
        "geo_analysis": "\ud83c\udf0d \u5730\u7406\u7a7a\u95f4\u5206\u6790\u4eea\u8868\u677f",
        "scatter_plot_header": "\ud83d\udccd 5. \u6309\u4f4d\u7f6e\u663e\u793a\u8d85\u901f\u4e8b\u4ef6",
        "heatmap": "\ud83d\udd25 6. \u8d85\u901f\u4e8b\u4ef6\u70e4\u529b\u56fe",
        "dynamic_table": "\ud83d\udcca 7. \u52a8\u6001\u8868\u683c\u67e5\u770b\u5668",
        "geo_heatmap_header": "\ud83c\udf0d \u5730\u7406\u7a7a\u95f4\u70e4\u529b\u56fe",
        "top_speeding_vehicles": "\ud83d\ude97 \u8d85\u901f\u6700\u591a\u768420\u8f66",
        # ... other translations ...
    }
}
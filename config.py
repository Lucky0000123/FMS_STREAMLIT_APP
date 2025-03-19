"""Configuration file for the FMS Safety Dashboard."""

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
    'driver': '{SQL Server}',
    'server': 'DESKTOP-JQDJV8F',
    'database': 'FMS_Safety',
    'trusted_connection': 'yes'
}

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
        "event_distribution": "📊 1. Total Event Distribution by Fleet Group",
        "event_distribution_detailed": "📊 2. Detailed Event Distribution by Fleet Group",
        "group_comparison": "📊 3. Total Speeding Events (Percentage and Count)",
        "time_series": "📈 4. Average Speeding Values Over Time",
        "geo_analysis": "🌍 Geo-Spatial Analysis Dashboard",
        "scatter_plot_header": "📍 5. Speeding Events by Location",
        "heatmap": "🔥 6. Speeding Event Heatmap",
        "dynamic_table": "📊 7. Dynamic Table Viewer",
        "geo_heatmap_header": "🌍 Geo-Spatial Heat Map",
        "top_speeding_vehicles": "🚗 Top 20 Vehicles with Most Speeding Events",
        # ... other translations ...
    },
    "ZH": {
        # ... existing Chinese translations ...
        "event_distribution": "📊 1. 按车队分组的总事件分布",
        "event_distribution_detailed": "📊 2. 按车队分组的详细事件分布",
        "group_comparison": "📊 3. 总超速事件(百分比和数量)",
        "time_series": "📈 4. 平均超速值随时间变化",
        "geo_analysis": "🌍 地理空间分析仪表板",
        "scatter_plot_header": "📍 5. 按位置显示超速事件",
        "heatmap": "🔥 6. 超速事件热力图",
        "dynamic_table": "📊 7. 动态表格查看器",
        "geo_heatmap_header": "🌍 地理空间热力图",
        "top_speeding_vehicles": "🚗 超速最多的20辆车",
        # ... other translations ...
    }
} 
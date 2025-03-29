"""
Translation dictionaries for the FMS Safety Dashboard
"""

from typing import Dict, Any

# English translations
EN_TRANSLATIONS = {
        # Common translations
        "language": "Language",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "loading": "🔄 Loading...",
        "success": "✅ Success!",
        "error": "⚠️ Error",
        "warning": "⚡ Warning",
        "info": "ℹ️ Information",
        
        # Sidebar translations
        "sidebar_title": "Dashboard Controls",
        "date_range": "Date Range",
        "start_date": "Start Date",
        "end_date": "End Date",
        "vehicle_selection": "Vehicle Selection",
        "all_vehicles": "All Vehicles",
        "fleet_groups": "Fleet Groups",
        "event_types": "Event Types",
        "apply_filters": "Apply Filters",
        "reset_filters": "Reset Filters",
        
        # Homepage translations
        "dashboard_title": "FMS Safety Dashboard",
        "dashboard_subtitle": "Real-time Fleet Management System Analytics",
        "kpi_section": "Key Performance Indicators",
        "total_events": "Total Events",
        "high_risk_events": "High Risk Events",
        "medium_risk_events": "Medium Risk Events",
        "low_risk_events": "Low Risk Events",
        "risk_distribution": "Risk Distribution",
        "event_trend": "Event Trend",
        "homepage_title": "🏠 Homepage",
        
        # Over Speeding Analysis translations
        "speeding_title": "Over Speeding Analysis",
        "speeding_events_by_day": "📈 Daily Speeding Events Analysis",
        "speeding_events_title": "Speeding Events Over Time",
        "speed_distribution": "Speed Distribution",
        "speed_trend": "Speed Trend",
        "top_speeders": "Top Speeders",
        "speed_by_time": "Speed by Time of Day",
        "speed_by_location": "Speed by Location",
        "extreme_speed": "Extreme Speed",
        "high_speed": "High Speed",
        "medium_speed": "Medium Speed",
        
        # Driver Analysis translations
        "driver_title": "Driver Performance Analysis",
        "driver_ranking": "Driver Ranking",
        "risk_score": "Risk Score",
        "safety_score": "Safety Score",
        "event_frequency": "Event Frequency",
        "driver_comparison": "Driver Comparison",
        "improvement_areas": "Areas for Improvement",
        "training_needs": "Training Needs",
        
        # Report Generation translations
        "report_title": "Report Generation",
        "generate_report": "Generate Report",
        "download_report": "Download Report",
        "report_period": "Report Period",
        "report_type": "Report Type",
        "include_charts": "Include Charts",
        "include_tables": "Include Tables",
        
        # Data Management translations
        "data_source": "Data Source",
        "sql_server": "SQL Server",
        "excel_file": "Excel File",
        "upload_file": "Upload File",
        "file_format": "File Format",
        "data_preview": "Data Preview",
        "refresh_data": "Refresh Data",
        
        # Error messages
        "no_data": "No data available for the selected filters",
        "invalid_date": "Invalid date range selected",
        "connection_error": "Failed to connect to the database",
        "upload_error": "Failed to upload file",
        "processing_error": "Error processing data",
        
        # Success messages
        "data_loaded": "Data loaded successfully",
        "filters_applied": "Filters applied successfully",
        "report_generated": "Report generated successfully",
        "file_uploaded": "File uploaded successfully",
        
        # Button labels
        "submit": "Submit",
        "cancel": "Cancel",
        "close": "Close",
        "save": "Save",
        "edit": "Edit",
        "delete": "Delete",
        "export": "Export",
        "print": "Print",
        
        # New translations for homepage
        "no_event_type_warning": "⚠️ No event type column found.",
        "required_columns_missing": "⚠️ Required columns not found for distribution.",
        "view_mode_label": "View Mode",
        "view_mode_all_groups": "Show All Groups",
        "view_mode_one_by_one": "Show One by One",
        "pdf_report_info": "PDF Report Information",
        "pdf_report_description": "Generate a professional PDF report containing all charts and visualizations from the dashboard.",
        "report_includes": "The report includes",
        "cover_page_info": "Cover page with logo and title",
        "table_of_contents": "Table of contents",
        "filter_info": "Filter information (date range, vehicles, fleet groups)",
        "kpi_info": "Key Performance Indicators (KPIs)",
        "charts_info": "All charts and visualizations",
        "page_numbers_info": "Page numbers and footer",
        "generation_time_info": "Generation time depends on the number of charts and data volume",
        "report_options": "Report Options",
        "select_report_type": "Select Report Type",
        "full_report": "Full Report",
        "lightweight_report": "Lightweight Report",
        "report_type_help": "Full report includes all charts. Lightweight report includes only essential charts for faster generation.",
        "include_maps": "Include Map Visualizations",
        "maps_help": "Including maps will increase the report generation time.",
        "generating_pdf": "Generating PDF report...",
        "pdf_generated": "PDF generated",
        "in_seconds": "in",
        "generation_tips": """
        💡 **Tip for faster report generation:**
        - Use the Lightweight Report option
        - Disable map visualizations
        - Apply more filters to reduce data volume
        """,
        "download_pdf_button": "⬇️ Download PDF Report",
        "event_distribution_detailed": "Detailed Event Distribution",
        "group_comparison": "Group Comparison",
        "top_speeding_vehicles": "Top Speeding Vehicles",
        "time_series": "Time Series Analysis",
        "scatter_plot_header": "Speeding Events Map",
        "heatmap": "Speeding Events Heatmap",
        "dynamic_table": "Dynamic Data Table",
        "report_generation": "Report Generation",
        
        # Homepage KPI translations
        "total_safety_events": "Total Safety Events",
        "total_speeding_events": "Total Speeding Events",
        "extreme_risk_events": "Extreme Risk Events",
        "fleet_most_violations": "Fleet with Most Violations",
        "avg_speed": "Average Speed",
        "avg_overspeed": "Average Overspeed",
        "top_offenders": "Top Offenders",
        
        # Homepage Chart translations
        "event_distribution": "📊 1. Total Event Distribution by Fleet Group",
        "event_distribution_detailed": "📊 2. Detailed Event Distribution by Fleet Group",
        "group_comparison": "📊 3. Total Speeding Events (Percentage and Count)",
        "time_series": "📈 4. Average Over-Speeding Values Over Time",
        "geo_analysis": "🌍 Geo-Spatial Analysis Dashboard",
        "scatter_plot_header": "📍 5. Speeding Events by Location",
        "heatmap": "🔥 6. Speeding Event Heatmap",
        "dynamic_table": "📊 7. Dynamic Table Viewer",
        "geo_heatmap_header": "🌍 Geo-Spatial Heat Map",
        "homepage_title": "🏠 Homepage",
        "download_reports_title": "📊 Download Reports",
        "top_speeding_vehicles": "🚗 Top 20 Vehicles with Most Speeding Events",
        
        # Group and Event Type translations
        "group_RIM": "RIM",
        "group_RIM-A": "RIM-A",
        "group_A": "Group A",
        "group_B": "Group B",
        "group_C": "Group C",
        
        "event_look_around": "Look Around",
        "event_closed_eyes": "Closed Eyes",
        "event_phone": "Phone",
        "event_yawn": "Yawn",
        "event_smoking": "Smoking",
        "event_bow_head": "Bow Head",
        "event_speeding": "Speeding",
        "event_occlusion": "Occlusion",
        "event_pcw": "PCW",
        "event_fcw": "FCW",
        "event_tired": "Tired",
        "event_overspeed_warning": "Overspeed warning in the area",
        "event_short_following": "Short Following Distance",
        
        # Driver Performance translations
        "driver_performance_title": "👨‍💼 Driver Performance & Warning Letters",
        "select_driver": "Select Driver",
        "driver_stats": "Driver Statistics",
        "total_violations": "Total Violations",
        "risk_score": "Risk Score",
        "safety_score": "Safety Score",
        "event_frequency": "Event Frequency",
        "driver_comparison": "Driver Comparison",
        "improvement_areas": "Areas for Improvement",
        "training_needs": "Training Needs",
        
        # Warning Letter translations
        "warning_letter_title": "Driver Warning Letter",
        "letter_date": "Date",
        "driver_name": "Driver Name",
        "vehicle_number": "Vehicle Number",
        "violation_details": "Violation Details",
        "warning_message": "Warning Message",
        "supervisor_signature": "Supervisor Signature",
        "acknowledgment": "Driver Acknowledgment",
        
        # Performance Report translations
        "performance_report_title": "Driver Performance Report",
        "report_summary": "Performance Summary",
        "recommendations": "Recommendations",
        "action_items": "Action Items",
        "follow_up": "Follow-up Actions",
        
        # New translations
        "loading_data": "Loading data from database...",
        "data_load_failed": "Failed to load data from database",
        "check_sql_connection": "Please check your SQL connection settings",
        "no_data_in_database": "The database contains no data",
        "check_database_content": "Please verify that the database contains the required data",
        "missing_required_columns": "The loaded data is missing required columns",
        "data_loaded_successfully": "Data loaded successfully!",
        "data_load_error": "Error occurred while loading data",
        
        # New translations for homepage
        "kpi_header": "Key Performance Indicators",
        "analytics_nav": "Analytics",
        "maps_nav": "Maps",
        "data_nav": "Data & Reports",
        
        # Driver Performance Page
        "performance_overview": "Performance Overview",
        "total_drivers": "Total Unique Drivers",
        "high_risk_drivers": "High Risk Drivers",
        "total_over_speeding_violations": "Total Over-Speeding Violations",
        "top_10_risky_drivers": "Top 10 Risky Drivers",
        "top_15_drivers_with_max_warning_letters": "Top 15 Drivers with Max Warning Letters",
        "warning_letters_summary": "Warning Letters Summary",
        "group": "Group",
        "shift": "Shift",
        "warnings": "Warnings",
        "no_warnings_selected_period": "No warnings found in the selected period",
        "overspeeding_violations": "Overspeeding Violations",
        "driver_event_analysis": "Driver Event Analysis",
        "event_type": "Event Type",
        "count": "Count",
        "event_breakdown_for": "Event Breakdown for",
        "driver": "Driver",
        "select_date_range": "Select Date Range",
        "check_over_speeding": "Check Over-Speeding Drivers",
        "summary_title": "Summary of Over-Speeding Letters",
        "violations_in_range": "Violations in Range",
        "named_drivers": "Named Drivers (session)",
        "unnamed_drivers": "Unnamed Drivers (session)",
        "total_warning_letters": "Total Warning Letters",
        "generate_pdf_named": "Generate PDF (Named Drivers)",
        "generate_pdf_unnamed": "Generate PDF (Unnamed Drivers)",
        "download_pdf_named": "Download PDF (Named Drivers)",
        "download_pdf_unnamed": "Download PDF (Unnamed Drivers)",
        "no_named_drivers": "未找到已知姓名驾驶员。请先点击\"检查超速驾驶员\"。",
        "no_unnamed_drivers": "未找到未知姓名驾驶员。请先点击\"检查超速驾驶员\"。",
        "generating_pdf": "生成PDF中...",
        "pdf_generation_complete": "PDF生成完成！",
        "overspeeding_threshold": "Overspeeding Threshold (Km/h)",

        # Page Titles and Headers
        "speeding_title": "Over Speeding Analysis",
        "click_for_translation": "Click here for Translation",

        # Overspeed Rating Section
        "overspeed_rating": "Overspeeding Risk Rating",
        "medium": "Medium",
        "high": "High",
        "extreme": "Extreme",
        "speed_range": "Speed Range",
        "kmh": "Km/h",

        # Shift Selection
        "select_shift": "Select Shift",
        "all_shifts": "All",
        "morning_shift": "Siang",
        "night_shift": "Malam",

        # Time Range Selection
        "select_time_range": "Select Time Range",
        "days": "Days",
        "select_range": "Select Range",

        # Loading States
        "loading_data": "Loading Data...",
        "loading_records": "Please wait while we fetch the latest safety records",
        "data_success": "✅ Data loaded successfully!",
        "no_data": "⚠️ No data available. Please check the data source.",

        # Descriptions
        "speed_description_medium": "Medium Risk: <10 km/h over limit",
        "speed_description_high": "High Risk: 10-20 km/h over limit",
        "speed_description_extreme": "Extreme Risk: ≥20 km/h over limit",

        # Over Speeding Page specific translations
        "overspeed_rating": "Overspeeding Risk Rating",
        "speed_description_medium": "Medium Risk: <10 km/h over limit",
        "speed_description_high": "High Risk: 10-20 km/h over limit",
        "speed_description_extreme": "Extreme Risk: ≥20 km/h over limit",
        "select_shift": "Select Shift",
        "select_time_range": "Select Time Range",
        "all_shifts": "All Shifts",
        "night_shift": "Night Shift",
        "morning_shift": "Day Shift",
        "date": "Date",
        "risk_level": "Risk Level",
        "number_of_events": "Number of Events",
        "trend": "Trend",
        "total_events": "Total Events",
        "overspeeding_intensity": "📊 Overspeeding Intensity by Fleet Group",
        "fleet_group": "Fleet Group",
        "events": "Events",
        "generate_pdf": "Generate PDF Report",
        "download_pdf": "Download PDF",
        "pdf_success": "PDF generated successfully!",
        "pdf_error": "Error generating PDF:",
        "pdf_cleanup_error": "Error cleaning up temporary files:",
        "no_data_warning": "⚠️ No data available for the selected filters.",
        "no_overspeeding_data": "⚠️ No overspeeding data available.",
        "no_data_for_report": "⚠️ No data available for report generation.",
        "column_not_found_error": "⚠️ Required column '{column}' not found in the dataset.",
        "data_processing_error": "⚠️ Error processing data: {error}",

        # Performance Dashboard Translations
        "performance_dashboard_title": "Driver Performance Dashboard",
        "performance_metrics": "Driver Performance Metrics",
        "performance_charts": "Performance Visualizations",
        "driver_performance": "Driver Analysis",

    # New translations
    "Est. time": "Estimated time",
    "Time elapsed": "Time elapsed",
    "Estimated remaining": "Estimated remaining",
    "Starting PDF generation for": "Starting PDF generation for",
    "named drivers": "named drivers",
    "unnamed drivers": "unnamed drivers",
    "Missing required columns": "Missing required columns",
    "No sidebar selections found!": "No sidebar selections found!",
    "Selected Date": "Selected Date",
    "Selected Date Range": "Selected Date Range",
    "Please select a date in the sidebar.": "Please select a date in the sidebar.",
    "Process in batches (recommended for large datasets)": "Process in batches (recommended for large datasets)",
    "Batch size": "Batch size",
    "No data available. Please load your dataset.": "No data available. Please load your dataset.",
    "Overspeeding Value": "Overspeeding Value",
    "Last 7 Days": "Last 7 Days",
    "Last 30 Days": "Last 30 Days",
    "Last 90 Days": "Last 90 Days",
    "Year to Date": "Year to Date",
    "Custom": "Custom",
    "low": "Low",

    # Additional sidebar translations
    "filter_help": "Use these filters to adjust the data displayed",
    "quick_filters": "Quick Filters",
    "advanced_filters": "Advanced Filters",
    "select_all": "Select All",
    "clear_all": "Clear All",
    "loading_filters": "Loading filter options...",
    "no_options": "No options available",
    "selected": "Selected",
    "items": "items",
    "sidebar_collapse": "Collapse Sidebar",
    "sidebar_expand": "Expand Sidebar",
    "menu": "Menu",
    "dashboard": "Dashboard",
    "reports": "Reports",
    "settings": "Settings",
    "help": "Help",
    "about": "About",
    "logout": "Logout",
    "profile": "Profile",
    "dark_mode": "Dark Mode",
    "light_mode": "Light Mode",
    "search": "Search",
    "select_language": "Select Language",
    "english": "English",
    "chinese": "Chinese",
    "last_updated": "Last Updated",
    "Select Vehicle": "Select Vehicle",

    # Theme and language selection
    "Theme Selection": "Theme Selection",
    "Current Theme": "Current Theme",
    "Language Settings": "Language Settings",
    "Current Language": "Current Language",
    
    # Date range options
    "This Week": "This Week",
    "This Month": "This Month",
    "Selected": "Selected",
    "Selected Shift": "Selected Shift",
    
    # Shift filter
    "Shift Filter": "Shift Filter",
    "All": "All",
    "Day": "Day",
    "Night": "Night",
    
    # Vehicle selection
    "Vehicle Selection": "Vehicle Selection",
    
    # Common date text
    "Jan": "1月",
    "Feb": "2月",
    "Mar": "3月",
    "Apr": "4月",
    "May": "5月",
    "Jun": "6月",
    "Jul": "7月",
    "Aug": "8月",
    "Sep": "9月",
    "Oct": "10月",
    "Nov": "11月",
    "Dec": "12月",
}

# Chinese translations
ZH_TRANSLATIONS = {
        # Common translations
        "language": "语言",
        "theme": "主题",
        "light": "明亮",
        "dark": "暗色",
        "loading": "🔄 加载中...",
        "success": "✅ 成功！",
        "error": "⚠️ 错误",
        "warning": "⚡ 警告",
        "info": "ℹ️ 信息",
        
        # Sidebar translations
        "sidebar_title": "仪表板控制",
        "date_range": "日期范围",
        "start_date": "开始日期",
        "end_date": "结束日期",
        "vehicle_selection": "车辆选择",
        "all_vehicles": "所有车辆",
        "fleet_groups": "车队组",
        "event_types": "事件类型",
        "apply_filters": "应用筛选",
        "reset_filters": "重置筛选",
        
        # Homepage translations
        "dashboard_title": "FMS 安全仪表板",
        "dashboard_subtitle": "实时车队管理系统分析",
        "kpi_section": "关键性能指标",
        "total_events": "总事件数",
        "high_risk_events": "高风险事件",
        "medium_risk_events": "中风险事件",
        "low_risk_events": "低风险事件",
        "risk_distribution": "风险分布",
        "event_trend": "事件趋势",
        "homepage_title": "🏠 主页",
        
        # Over Speeding Analysis translations
        "speeding_title": "超速分析",
        "speeding_events_by_day": "📈 每日超速事件分析",
        "speeding_events_title": "随时间变化的超速事件",
        "speed_distribution": "速度分布",
        "speed_trend": "速度趋势",
        "top_speeders": "最高速度者",
        "speed_by_time": "按时间速度",
        "speed_by_location": "按位置速度",
        "extreme_speed": "极端速度",
        "high_speed": "高速",
        "medium_speed": "中速",
        
        # Driver Analysis translations
        "driver_title": "驾驶员表现分析",
        "driver_ranking": "驾驶员排名",
        "risk_score": "风险评分",
        "safety_score": "安全评分",
        "event_frequency": "事件频率",
        "driver_comparison": "驾驶员比较",
        "improvement_areas": "需改进的领域",
        "training_needs": "培训需求",
        
        # Report Generation translations
        "report_title": "报告生成",
        "generate_report": "生成报告",
        "download_report": "下载报告",
        "report_period": "报告期",
        "report_type": "报告类型",
        "include_charts": "包括图表",
        "include_tables": "包括表格",
        
        # Data Management translations
        "data_source": "数据源",
        "sql_server": "SQL Server",
        "excel_file": "Excel 文件",
        "upload_file": "上传文件",
        "file_format": "文件格式",
        "data_preview": "数据预览",
        "refresh_data": "刷新数据",
        
        # Error messages
        "no_data": "没有可用数据",
        "invalid_date": "无效的日期范围",
        "connection_error": "无法连接到数据库",
        "upload_error": "上传文件失败",
        "processing_error": "数据处理错误",
        
        # Success messages
        "data_loaded": "数据加载成功",
        "filters_applied": "筛选器应用成功",
        "report_generated": "报告生成成功",
        "file_uploaded": "文件上传成功",
        
        # Button labels
        "submit": "提交",
        "cancel": "取消",
        "close": "关闭",
        "save": "保存",
        "edit": "编辑",
        "delete": "删除",
        "export": "导出",
        "print": "打印",
        
        # Driver Performance translations
        "driver_performance_title": "👨‍💼 驾驶员表现与警告信",
        "select_driver": "选择驾驶员",
        "driver_stats": "驾驶员统计",
        "total_violations": "总违规数",
        "risk_score": "风险评分",
        "safety_score": "安全评分",
        "event_frequency": "事件频率",
        "driver_comparison": "驾驶员比较",
        "improvement_areas": "需改进的领域",
        "training_needs": "培训需求",
        
        # Driver Performance Page
        "click_for_translation": "点击切换语言",
        "performance_overview": "绩效概览",
        "total_drivers": "总驾驶员人数",
        "high_risk_drivers": "高风险驾驶员",
        "total_over_speeding_violations": "总超速违规",
        "top_10_risky_drivers": "风险排名前10驾驶员",
        "top_15_drivers_with_max_warning_letters": "警告信数量最多的前15名驾驶员",
        "warning_letters_summary": "警告信汇总",
        "group": "组别",
        "shift": "班次",
        "warnings": "警告数",
        "no_warnings_selected_period": "在选定的时期内未找到警告",
        "overspeeding_violations": "超速违规",
        "driver_event_analysis": "驾驶员事件分析",
        "event_type": "事件类型",
        "count": "数量",
        "event_breakdown_for": "事件明细 - ",
        "driver": "驾驶员",
        "select_date_range": "选择日期范围",
        "check_over_speeding": "检查超速驾驶员",
        "summary_title": "📊 超速警告信摘要",
        "violations_in_range": "范围内违规数",
        "named_drivers": "已知姓名驾驶员（会话）",
        "unnamed_drivers": "未知姓名驾驶员（会话）",
        "total_warning_letters": "总警告信数",
        "generate_pdf_named": "生成PDF（已知姓名驾驶员）",
        "generate_pdf_unnamed": "生成PDF（未知姓名驾驶员）",
        "download_pdf_named": "下载PDF（已知姓名驾驶员）",
        "download_pdf_unnamed": "下载PDF（未知姓名驾驶员）",
        "no_named_drivers": "未找到已知姓名驾驶员。请先点击\"检查超速驾驶员\"。",
        "no_unnamed_drivers": "未找到未知姓名驾驶员。请先点击\"检查超速驾驶员\"。",
        "generating_pdf": "生成PDF中...",
        "pdf_generation_complete": "PDF生成完成！",
        "overspeeding_threshold": "超速國值（公里/小时）",

        # Page Titles and Headers
        "speeding_title": "超速分析",
        "click_for_translation": "点击此处翻译",

        # Overspeed Rating Section
        "overspeed_rating": "超速风险评级",
        "medium": "中等",
        "high": "高",
        "extreme": "极高",
        "speed_range": "速度范围",
        "kmh": "公里/小时",

        # Shift Selection
        "select_shift": "选择班次",
        "all_shifts": "全部",
        "morning_shift": "白班",
        "night_shift": "夜班",

        # Time Range Selection
        "select_time_range": "选择时间范围",
        "days": "天",
        "select_range": "选择范围",

        # Additional translations
        "Total Incidents": "总事件数",
        "High Risk Drivers": "高风险驾驶员",
        "Avg Overspeeding/Driver": "平均超速/驾驶员",
        "Extreme Risk Events": "极高风险事件",
        "Date": "日期",
        "Number of Incidents": "事件数量",
        "Daily Incident Trend": "日常事件趋势",
        "Incidents by Overspeeding Severity": "按超速严重程度分类的事件",
        "Overspeeding Severity": "超速严重程度",
        "Date information is not available in the data": "数据中没有日期信息",
        "Overspeeding value information is not available in the data": "数据中没有超速值信息",
        "Date Selection": "日期选择",
        "Select Date Type": "选择日期类型",
        "Single Date": "单一日期",
        "Select Date": "选择日期",
        "Select Time Period": "选择时间段",
        "Select Fleet Group": "选择车队组",
        "No Group information available in the data": "数据中没有组信息",
        "Select Risk Level": "选择风险级别",
        "Est. time": "预计时间",
        "Time elapsed": "已用时间",
        "Estimated remaining": "预计剩余时间",
        "Starting PDF generation for": "开始为以下驾驶员生成PDF",
        "named drivers": "已知姓名驾驶员",
        "unnamed drivers": "未知姓名驾驶员",
        "Missing required columns": "缺少必需的列",
        "No sidebar selections found!": "未找到侧边栏选择！",
        "Selected Date": "选定日期",
        "Selected Date Range": "选定日期范围",
        "Please select a date in the sidebar.": "请在侧边栏中选择日期。",
        "Process in batches (recommended for large datasets)": "批处理（推荐用于大数据集）",
        "Batch size": "批处理大小",
        "No data available. Please load your dataset.": "没有可用数据。请加载您的数据集。",
        "Overspeeding Value": "超速值",
        "Last 7 Days": "最近7天",
        "Last 30 Days": "最近30天",
        "Last 90 Days": "最近90天",
        "Year to Date": "今年至今",
        "Custom": "自定义",
        "low": "低",

        # Performance Dashboard Translations
        "performance_dashboard_title": "驾驶员绩效仪表板",
        "performance_metrics": "驾驶员绩效指标",
        "performance_charts": "绩效可视化",
        "driver_performance": "驾驶员分析",
        
        # New translations
        "Est. time": "预计时间",
        "total_safety_events": "总安全事件",
        "total_speeding_events": "总超速事件",
        "extreme_risk_events": "极端风险事件",
        "fleet_most_violations": "违规最多的车队",
        "avg_speed": "平均速度",
        "avg_overspeed": "平均超速",
        "top_offenders": "违规最多的司机",

        # Add missing translation key for event_distribution
        "event_distribution": "📊 1. 按车队组划分的总事件分布",
        
        # Homepage KPI translations
        "total_safety_events": "总安全事件",
        "total_speeding_events": "总超速事件",
        "extreme_risk_events": "极端风险事件",
        "fleet_most_violations": "违规最多的车队",
        "avg_speed": "平均速度",
        "avg_overspeed": "平均超速",
        "top_offenders": "违规最多的司机",
        
        # Homepage Chart translations
        "event_distribution": "📊 1. 按车队组划分的总事件分布",
        "event_distribution_detailed": "📊 2. 按车队组划分的详细事件分布",
        "group_comparison": "📊 3. 总超速事件（百分比和数量）",
        "time_series": "📈 4. 超速值随时间的平均变化",
        "geo_analysis": "🌍 地理空间分析仪表板",
        "scatter_plot_header": "📍 5. 按位置划分的超速事件",
        "heatmap": "🔥 6. 超速事件热图",
        "dynamic_table": "📊 7. 动态表格查看器",
        "geo_heatmap_header": "🌍 地理空间热图",
        "homepage_title": "🏠 主页",
        "download_reports_title": "📊 下载报告",
        "top_speeding_vehicles": "🚗 超速事件最多的前20辆车辆",
        
        # New translations for homepage
        "no_event_type_warning": "⚠️ 未找到事件类型列。",
        "required_columns_missing": "⚠️ 未找到分布所需的列。",
        "view_mode_label": "查看模式",
        "view_mode_all_groups": "显示所有组",
        "view_mode_one_by_one": "逐个显示",
        "pdf_report_info": "PDF报告信息",
        "pdf_report_description": "生成包含仪表板所有图表和可视化的专业PDF报告。",
        "report_includes": "报告包含",
        "cover_page_info": "带有徽标和标题的封面",
        "table_of_contents": "目录",
        "filter_info": "筛选信息（日期范围、车辆、车队组）",
        "kpi_info": "关键绩效指标（KPI）",
        "charts_info": "所有图表和可视化",
        "page_numbers_info": "页码和页脚",
        "generation_time_info": "生成时间取决于图表数量和数据量",
        "report_options": "报告选项",
        "select_report_type": "选择报告类型",
        "full_report": "完整报告",
        "lightweight_report": "精简报告",
        "report_type_help": "完整报告包括所有图表。精简报告仅包括基本图表，以加快生成速度。",
        "include_maps": "包含地图可视化",
        "maps_help": "包含地图将增加报告生成时间。",
        "generating_pdf": "正在生成PDF报告...",
        "pdf_generated": "PDF已生成",
        "in_seconds": "耗时",
        "generation_tips": """
        💡 **加快报告生成的提示:**
        - 使用精简报告选项
        - 禁用地图可视化
        - 应用更多筛选器以减少数据量
        """,
        "download_pdf_button": "⬇️ 下载PDF报告",
        "report_generation": "报告生成",
        "kpi_header": "关键绩效指标",
        "analytics_nav": "分析",
        "maps_nav": "地图",
        "data_nav": "数据与报告",

        # Additional sidebar translations
        "filter_help": "使用这些筛选器来调整显示的数据",
        "quick_filters": "快速筛选",
        "advanced_filters": "高级筛选",
        "select_all": "全选",
        "clear_all": "清除全部",
        "loading_filters": "加载筛选选项...",
        "no_options": "没有可用选项",
        "selected": "已选择",
        "items": "项",
        "sidebar_collapse": "收起侧边栏",
        "sidebar_expand": "展开侧边栏",
        "menu": "菜单",
        "dashboard": "仪表板",
        "reports": "报告",
        "settings": "设置",
        "help": "帮助",
        "about": "关于",
        "logout": "退出",
        "profile": "个人资料",
        "dark_mode": "暗色模式",
        "light_mode": "明亮模式",
        "search": "搜索",
        "select_language": "选择语言",
        "english": "英语",
        "chinese": "中文",
        "last_updated": "最后更新",
        "Select Vehicle": "选择车辆",
        "refresh_data": "刷新数据",

        # Theme and language selection
        "Theme Selection": "主题选择",
        "Current Theme": "当前主题",
        "Current Theme: Light": "当前主题：明亮",
        "Current Theme: Dark": "当前主题：暗色",
        "Language Settings": "语言设置",
        "Current Language": "当前语言",
        
        # Date range options
        "This Week": "本周",
        "This Month": "本月",
        "Selected": "已选择",
        "Selected Shift": "已选择班次",
        "Selected: ": "已选择：",
        
        # Shift filter
        "Shift Filter": "班次筛选",
        "All": "全部",
        "Day": "白天",
        "Night": "夜间",
        "Selected Shift: All": "已选择班次：全部",
        "Selected Shift: ": "已选择班次：",
        
        # Vehicle selection
        "Vehicle Selection": "车辆选择",
        
        # Common date text
        "Jan": "1月",
        "Feb": "2月",
        "Mar": "3月",
        "Apr": "4月",
        "May": "5月",
        "Jun": "6月",
        "Jul": "7月",
        "Aug": "8月",
        "Sep": "9月",
        "Oct": "10月",
        "Nov": "11月",
        "Dec": "12月",

        # Missing translations for the Over Speeding Analysis page
        "speeding_events_by_day": "📈 每日超速事件分析",
        "speeding_events_title": "随时间变化的超速事件",
        "overspeeding_intensity": "📊 按车队组划分的超速强度",
        "fleet_group": "车队组",
        "trend": "趋势",
        "events": "事件",
        "number_of_events": "事件数量",
        "total_events": "总事件数",
        "risk_level": "风险级别",
        "date": "日期",
        
        # For the PDF generation
        "generate_pdf": "生成PDF报告",
        "download_pdf": "下载PDF",

        # Additional homepage elements
        "loading_data": "加载数据中...",
        "data_load_failed": "从数据库加载数据失败",
        "check_sql_connection": "请检查您的SQL连接设置",
        "no_data_in_database": "数据库中没有数据",
        "check_database_content": "请确认数据库包含所需数据",
        "missing_required_columns": "加载的数据缺少必需的列",
        "data_loaded_successfully": "数据加载成功！",
        "data_load_error": "加载数据时出错",
        "upload_file": "上传文件",
        "file_format": "文件格式",
        "data_preview": "数据预览",
        "refresh_data": "刷新数据",

        # Calendar UI elements
        "Day": "日",
        "Week": "周",
        "Month": "月",
        "Year": "年",
        "Today": "今天",
        "Yesterday": "昨天",
        "Tomorrow": "明天",
        "Cancel": "取消",
        "Clear": "清除",
        "Custom Range": "自定义范围",
        "Apply": "应用",
        "From": "从",
        "To": "至"
}

# Combine all translations into a single dictionary
TRANSLATIONS = {
    "EN": EN_TRANSLATIONS,
    "ZH": ZH_TRANSLATIONS
}

def get_translation(key: str, language: str = "EN") -> str:
    """
    Get the translation for a given key in the specified language.
    
    Args:
        key (str): The translation key to look up
        language (str): The target language (defaults to "EN")
        
    Returns:
        str: The translated text, or the key itself if no translation is found
    """
    # Get the translations dictionary for the specified language
    lang_dict = TRANSLATIONS.get(language, TRANSLATIONS["EN"])
    
    # Try to get the translation, return the key if not found
    return lang_dict.get(key, key)

def get_group_translation(group: str, language: str = "EN") -> str:
    """
    Get the translation for a group name.
    
    Args:
        group (str): The group name to translate
        language (str): The target language (defaults to "EN")
        
    Returns:
        str: The translated group name
    """
    key = f"group_{group}"
    return get_translation(key, language)

def get_event_translation(event: str, language: str = "EN") -> str:
    """
    Get the translation for an event type.
    
    Args:
        event (str): The event type to translate
        language (str): The target language (defaults to "EN")
        
    Returns:
        str: The translated event type
    """
    key = f"event_{event.lower().replace(' ', '_')}"
    return get_translation(key, language)